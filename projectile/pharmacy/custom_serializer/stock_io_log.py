from validator_collection import checkers
from django.db.models.functions import Coalesce
from django.db.models import Sum
from rest_framework import serializers

from common.enums import Status
from core.models import Organization
from .stock import StockWithProductUnitForCartV2Serializer
from .unit import UnitModelSerializer
from ..utils import (
    construct_stock_object_from_dictionary,
    construct_product_object_from_dictionary,
    construct_store_point_object_from_dictionary,
)
from ..models import StockIOLog, Stock
from ..enums import StockIOType
from pharmacy.serializers import StockIOLogSerializer, UnitSerializer
from pharmacy.custom_serializer.stock import (
    StockForCartGetSerializer,
    StockForInvoicePDFSerializer,
)

#pylint: disable=W0223
class StockIoLogReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    amount = serializers.FloatField()
    qty = serializers.IntegerField()
    discount = serializers.FloatField()
    vat = serializers.FloatField()
    storepoint = serializers.CharField(source='purchase__store_point__name')
    supplier = serializers.CharField(source='purchase__person_organization_supplier__company_name')
    stock = serializers.SerializerMethodField()

    def get_stock(self, obj):
        return construct_stock_object_from_dictionary(obj)


#pylint: disable=W0223
class ProductWiseStockTransferReportSerializer(serializers.Serializer):
    transfer__date = serializers.DateField()
    transfer_from = serializers.SerializerMethodField()
    transfer_to = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_quantity = serializers.IntegerField()
    unit_name = serializers.CharField()

    def get_product(self, _obj):
        return construct_product_object_from_dictionary(_obj, 'stock__')

    def get_transfer_from(self, _obj):
        fields_dict = {
            'id': 'transfer__transfer_from',
            'alias': 'transfer__transfer_from__alias',
            'name': 'transfer__transfer_from__name'
        }
        return construct_store_point_object_from_dictionary(_obj, fields_dict)

    def get_transfer_to(self, _obj):
        fields_dict = {
            'id': 'transfer__transfer_to',
            'alias': 'transfer__transfer_to__alias',
            'name': 'transfer__transfer_to__name'
        }
        return construct_store_point_object_from_dictionary(_obj, fields_dict)


class DistributorOrderCartPostV2Serializer(serializers.ModelSerializer):

    def validate_quantity(self, value):
        from pharmacy.views import DistributorOrderLimitPerDay

        if not 'is_queueing_order' in self.initial_data:
            request = self.context.get('request')
            _stock_id = self.initial_data.get('stock')
            qty = self.initial_data.get('quantity', 0)
            self.request = request
            data = DistributorOrderLimitPerDay.get(self, request, _stock_id)
            add_to_queue = data.data.get('add_to_queue', False)
            order_limit = data.data.get('order_limit', 0)
            order_quantity = data.data.get('order_quantity', 0)
            is_valid_qty =  order_quantity + qty <= order_limit
            self.initial_data['is_queueing_order'] = add_to_queue
            if not is_valid_qty:
                raise serializers.ValidationError(
                    'You can order 0 more of this product'
                )
        return value

    class Meta:
        model = StockIOLog
        fields = (
            'stock',
            'quantity',
        )

    def create(self, validated_data):
        from pharmacy.utils import get_or_create_cart_instance

        request = self.context.get("request")
        # For app version 1.16.0 where no io_alias is available
        if not 'stock_io_alias' in request.data:
            cart_group_data = {}
            cart_group_data['entry_by'] = request.user
            org_id = request.user.organization_id
            organization_instance = Organization.objects.only('pk').get(pk=org_id)
            cart_group_id = organization_instance.get_or_add_cart_group(cart_group_data, ['id'], True)
            distributor_id = request.data.get('distributor', 303)
            user_id = request.user.id
            is_queueing_order_value = request.data.get('is_queueing_order', False)
            cart_instance_id = get_or_create_cart_instance(
                org_id, distributor_id, cart_group_id, user_id, is_queueing_order_value, True)
            _stock_id = validated_data.get('stock')
            try:
                existing_log = StockIOLog.objects.only(
                    'quantity',
                ).get(
                    purchase__id=cart_instance_id,
                    status=Status.DISTRIBUTOR_ORDER,
                    type=StockIOType.INPUT,
                    organization__id=request.user.organization_id,
                    stock=_stock_id
                )
                qty = validated_data.get('quantity', 0)
                if qty:
                    existing_log.quantity = qty
                    StockIOLog.objects.bulk_update(
                        [existing_log],
                        ['quantity',],
                        batch_size=1
                    )
                else:
                    existing_log.status = Status.INACTIVE
                    StockIOLog.objects.bulk_update(
                        [existing_log],
                        ['status',],
                        batch_size=1
                    )
            except (StockIOLog.DoesNotExist):
                create_cart_item_instances = []
                create_cart_item_instances.append(StockIOLog(
                    purchase_id=cart_instance_id,
                    status=Status.DISTRIBUTOR_ORDER,
                    type=StockIOType.INPUT,
                    organization_id=request.user.organization_id,
                    entry_by_id=request.user.id,
                    batch="N/A",
                    **validated_data
                ))
                existing_log = StockIOLog.objects.bulk_create(create_cart_item_instances)

            except (StockIOLog.MultipleObjectsReturned):
                existing_logs = StockIOLog.objects.filter(
                    purchase__id=cart_instance_id,
                    status=Status.DISTRIBUTOR_ORDER,
                    type=StockIOType.INPUT,
                    organization__id=request.user.organization_id,
                    stock=_stock_id
                )
                # total_qty = existing_logs.values('stock_id').order_by().aggregate(
                #     total_quantity = Coalesce(Sum('quantity'), 0)
                # ).get('total_quantity', 0)
                existing_log = existing_logs.first()
                qty = validated_data.get('quantity', 0)
                if qty:
                    existing_log.quantity = qty
                    StockIOLog.objects.bulk_update(
                        [existing_log],
                        ['quantity',],
                        batch_size=1
                    )
                else:
                    existing_log.status = Status.INACTIVE
                    StockIOLog.objects.bulk_update(
                        [existing_log],
                        ['status',],
                        batch_size=1
                    )
                item_pks = existing_logs.values_list('pk', flat=True)
                pk_list = list(item_pks[1:])
                StockIOLog.objects.filter(pk__in=pk_list).update(status=Status.INACTIVE)

            return existing_log
        stock_io_alias = request.data.get('stock_io_alias', '')
        if checkers.is_uuid(stock_io_alias):
            try:
                existing_log = StockIOLog.objects.only(
                    'quantity',
                ).get(
                    alias=stock_io_alias,
                )
                existing_log.quantity = validated_data.get('quantity')
                StockIOLog.objects.bulk_update(
                    [existing_log],
                    ['quantity',],
                    batch_size=1
                )
            except:
                pass
        else:
            cart_group_data = {}
            cart_group_data['entry_by'] = request.user
            org_id = request.user.organization_id
            organization_instance = Organization.objects.only('pk').get(pk=org_id)
            cart_group_id = organization_instance.get_or_add_cart_group(cart_group_data, ['id'], True)
            distributor_id = request.data.get('distributor')
            user_id = request.user.id
            is_queueing_order_value = request.data.get('is_queueing_order', False)
            cart_instance_id = get_or_create_cart_instance(
                org_id, distributor_id, cart_group_id, user_id, is_queueing_order_value, True)
            create_cart_item_instances = []
            create_cart_item_instances.append(StockIOLog(
                purchase_id=cart_instance_id,
                status=Status.DISTRIBUTOR_ORDER,
                type=StockIOType.INPUT,
                organization_id=org_id,
                entry_by_id=user_id,
                batch="N/A",
                **validated_data
            ))
            existing_log = StockIOLog.objects.bulk_create(create_cart_item_instances)
        return existing_log


class StockIOLogForCardV2Serializer(serializers.ModelSerializer):
    quantity = serializers.FloatField(min_value=0)
    stock = StockWithProductUnitForCartV2Serializer()
    primary_unit = UnitModelSerializer.MinimalList()
    secondary_unit = UnitModelSerializer.MinimalList()

    class Meta:
        model = StockIOLog
        fields = (
            'id',
            'alias',
            'stock',
            'quantity',
            'rate',
            'batch',
            'date',
            'discount_rate',
            'discount_total',
            'round_discount',
            'primary_unit',
            'secondary_unit',
            'conversion_factor',
        )


class ProcessingToDeliverStockListSerializer(serializers.ModelSerializer):

    class Meta:
        model = StockIOLog
        fields = (
            'stock',
            'quantity',
        )

class StockIOLogForCartPostSerializer(serializers.ModelSerializer):
    stock = serializers.PrimaryKeyRelatedField(
        queryset=Stock().get_all_actives().only(
            "id",
        )
    )
    class Meta:
        model = StockIOLog
        fields = (
            'stock',
            'quantity',
            'rate',
            'batch',
            'date',
            'type',
        )

class StockIOLogForCartGetSerializer(StockIOLogSerializer):
    stock = StockForCartGetSerializer()
    primary_unit = UnitSerializer()
    secondary_unit = UnitSerializer()

    class Meta:
        model = StockIOLog
        fields = (
            'id',
            'alias',
            'stock',
            'quantity',
            'rate',
            'primary_unit',
            'secondary_unit',
            'discount_rate',
            'discount_total',
            'vat_rate',
            'vat_total',
            'tax_total',
            'tax_rate',
            'round_discount',
            'batch',
            'base_discount',
        )


class StockIOLogForInvoicePDFSerializer(StockIOLogSerializer):
    stock = StockForInvoicePDFSerializer()

    class Meta:
        model = StockIOLog
        fields = (
            'stock',
            'quantity',
            'rate',
            'discount_total',
            'round_discount',
            'discount_rate',
        )
