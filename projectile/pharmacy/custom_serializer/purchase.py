import os
import time
import uuid
from datetime import datetime, timedelta
from copy import copy
from functools import reduce
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.db import transaction
from django.core.cache import cache
from rest_framework import serializers
from rest_framework.serializers import Serializer

from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)
from common.enums import Status
from common.helpers import to_boolean, versiontuple
from common.healthos_helpers import CustomerHelper, HealthOSHelper
from common.utils import get_healthos_settings
from common.cache_keys import (
    USER_ORDER_ID_LIST_CACHE_KEY_PREFIX,
)
from core.custom_serializer.organization import OrganizationModelSerializer
from core.models import Organization, Person, PersonOrganization
from core.serializers import (
    PersonOrganizationEmployeeSearchSerializer,
    DepartmentSerializer,
    PersonOrganizationEmployeeSerializer,
    PersonOrganizationLiteSerializer,
)
from core.utils import construct_organization_object_from_dictionary
from core.enums import AllowOrderFrom

from delivery.serializers.stock_delivery import StockDeliveryModelSerializer

from ..models import (
    Purchase,
    StockIOLog,
    DistributorOrderGroup,
    OrderTracking,
    StorePoint,
)
from ..enums import StockIOType, DistributorOrderType, PurchaseType, SystemPlatforms, OrderTrackingStatus
from ..serializers import StockIOLogSerializer, StockIOLogDetailsWithUnitDetailsSerializer, StorePointSerializer
from .stock_io_log import (
    StockIOLogForCardV2Serializer,
    StockIOLogForCartPostSerializer,
    StockIOLogForInvoicePDFSerializer,
)
from .order_tracking import OrderTrackingModelSerializer
from ..utils import get_tentative_delivery_date, get_cart_group_id, get_or_create_cart_instance
from pharmacy.tasks import apply_additional_discount_on_order
from pharmacy.custom_serializer.stock_io_log import StockIOLogForCartGetSerializer

class PurchaseMeta(ListSerializer.Meta):
    model = Purchase
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


#pylint: disable=W0223
class PurchaseSummarySerializer(Serializer):
    purchase_date = serializers.DateField()
    supplier = serializers.CharField()
    store = serializers.CharField()
    purchase_count = serializers.IntegerField()
    total_discount = serializers.FloatField()
    total_vat = serializers.FloatField()
    total_purchase = serializers.FloatField()
    grand_total = serializers.FloatField()


class DistributorOrderCartPostSerializer(serializers.ModelSerializer):
    from common.custom_serializer_field import CustomRelatedField

    stock_io_logs = StockIOLogForCartPostSerializer(many=True)
    # receiver = CustomRelatedField(
    #     model=Person,
    # )
    # person_organization_receiver = CustomRelatedField(
    #     model=PersonOrganization,
    # )
    # store_point = CustomRelatedField(
    #     model=StorePoint,
    # )

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            # 'receiver',
            # 'person_organization_receiver',
            'stock_io_logs',
            'transport',
            # 'store_point',
            'distributor',
            # 'is_queueing_order',
        )

    def create(self, validated_data):
        request = self.context.get("request")
        user_org_id = request.user.organization_id
        cart_group_id = get_cart_group_id(user_org_id)
        distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)

        stock_io_logs = validated_data.pop('stock_io_logs', [])
        cart_instance_id = get_or_create_cart_instance(
            org_id=user_org_id,
            dist_id=distributor_id,
            cart_group_id=cart_group_id,
            user_id=request.user.id,
            # is_queueing_order=is_queueing_order,
            set_cache=True
        )
        if not cart_instance_id:
            user_organization = Organization.objects.only("pk").get(
                pk=user_org_id
            )
            validated_data['distributor_order_group_id'] = cart_group_id
            validated_data['entry_by_id'] = request.user.id
            validated_data['distributor_id'] = distributor_id
            validated_data['is_queueing_order'] = False
            cart_instance = user_organization.get_or_add_distributorwise_cart(validated_data)
            cart_instance_id=cart_instance.id
        io_select_fields = [
            "id",
            "quantity",
        ]
        # create stock io logs(cart items) in reverse order
        for item in reversed(stock_io_logs):
            cart_item = copy(item)
            _stock_id = cart_item.pop('stock')
            try:
                existing_log = StockIOLog.objects.only(*io_select_fields).get(
                    purchase__id=cart_instance_id,
                    status=Status.DISTRIBUTOR_ORDER,
                    type=StockIOType.INPUT,
                    organization_id=request.user.organization_id,
                    stock=_stock_id
                )
                cart_item.pop('date')
                existing_log.__dict__.update(**cart_item)
                StockIOLog.objects.bulk_update(
                    [existing_log],
                    ["quantity"],
                    batch_size=10
                )
            except (StockIOLog.DoesNotExist):
                data = StockIOLog(
                    purchase_id=cart_instance_id,
                    status=Status.DISTRIBUTOR_ORDER,
                    type=StockIOType.INPUT,
                    organization_id=request.user.organization_id,
                    entry_by_id=request.user.id,
                    **item
                )
                existing_log = StockIOLog.objects.bulk_create(
                    [data]
                )

            except (StockIOLog.MultipleObjectsReturned):
                existing_logs = StockIOLog.objects.only(*io_select_fields).filter(
                    purchase__id=cart_instance_id,
                    status=Status.DISTRIBUTOR_ORDER,
                    type=StockIOType.INPUT,
                    organization_id=request.user.organization_id,
                    stock=_stock_id
                ).order_by('-pk')
                existing_log = existing_logs.first()
                existing_log.__dict__.update(**cart_item)
                StockIOLog.objects.bulk_update(
                    [existing_log],
                    ["quantity"],
                    batch_size=10
                )
                item_pks = existing_logs.values_list('pk', flat=True)
                pk_list = list(item_pks[1:])
                StockIOLog.objects.filter(pk__in=pk_list).update(status=Status.INACTIVE)

        return existing_log


class DistributorOrderCartSerializer(serializers.ModelSerializer):
    stock_io_logs = StockIOLogForCartGetSerializer(many=True)
    distributor = OrganizationModelSerializer.Lite(read_only=True)
    # order_status = OrderTrackingModelSerializer.List(many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'stock_io_logs',
            'distributor',
            'additional_discount',
            'additional_discount_rate',
            'additional_cost',
            'additional_cost_rate',
            # 'order_status',
            'current_order_status',
            'receiver',
            'store_point',
            'person_organization_receiver',
            'is_queueing_order',
            'tentative_delivery_date',
            'discount_info',
            'order_rating',
            'order_rating_comment',
            'dynamic_discount_amount',
        )


class DistributorOrderCartGetSerializer(serializers.ModelSerializer):
    order_groups = DistributorOrderCartSerializer(many=True)
    organization = OrganizationModelSerializer.LiteWithMinOrderAmount()

    class Meta:
        model = DistributorOrderGroup
        fields = (
            'id',
            'alias',
            'status',
            'sub_total',
            'discount',
            'round_discount',
            'transport',
            'order_groups',
            'organization',
            'show_cart_warning',
        )
        read_only_fields = (
            'transport',
            'organization',
            'show_cart_warning',
        )

class DistributorOrderCartV2Serializer(serializers.ModelSerializer):
    stock_io_logs = StockIOLogForCardV2Serializer(many=True)
    distributor = OrganizationModelSerializer.Lite(read_only=True)

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'grand_total',
            'stock_io_logs',
            'distributor',
            'store_point',
            'is_queueing_order',
            'tentative_delivery_date',
        )

class DistributorOrderCartGetV2Serializer(serializers.ModelSerializer):
    order_groups = DistributorOrderCartV2Serializer(many=True)
    organization = OrganizationModelSerializer.LiteWithMinOrderAmount()

    class Meta:
        model = DistributorOrderGroup
        fields = (
            'id',
            'alias',
            'status',
            'sub_total',
            'discount',
            'round_discount',
            'transport',
            'order_groups',
            'organization',
        )
        read_only_fields = (
            'transport',
            'organization',
        )


class DeliveryOrderListSerializer(serializers.ModelSerializer):
    geo_location_data = serializers.DictField()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'grand_total',
            'geo_location_data',
        )
        read_only_fields = (
            'id',
            'alias',
            'purchase_date',
        )


class DeliveryOrderDetailsSerializer(serializers.ModelSerializer):

    geo_location_data = serializers.DictField()
    products = StockDeliveryModelSerializer.Details(many=True)

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'grand_total',
            'geo_location_data',
            'products',
        )
        read_only_fields = (
            'id',
            'alias',
            'purchase_date',
        )


class DistributorOrderListSerializer(serializers.ModelSerializer):
    from core.models import Person, PersonOrganization

    stock_io_logs = StockIOLogSerializer(many=True)
    person_organization_receiver = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=PersonOrganization.objects.filter().only('id')
    )
    receiver = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Person.objects.filter().only('id')
    )
    distributor = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Organization.objects.filter().only('id',)
    )

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'receiver',
            'person_organization_receiver',
            'stock_io_logs',
            'transport',
            'store_point',
            'distributor',
            'is_queueing_order',
            'dynamic_discount_amount',
        )
        read_only_fields = (
            'id',
            'alias',
            'purchase_date',
        )


class DistributorOrderGroupPostSerializer(serializers.ModelSerializer):
    order_groups = DistributorOrderListSerializer(many=True)

    class Meta:
        model = DistributorOrderGroup
        fields = (
            'id',
            'alias',
            'status',
            'sub_total',
            'discount',
            'round_discount',
            'order_groups',
        )

    def prepare_order_groups(self, group_data, orders):

        group_code = uuid.uuid4()
        order_groups = []
        order_items = []
        for order in orders:
            io_logs = order.get('stock_io_logs', [])
            order_items.extend(io_logs)
            order_groups.append(
                {
                    "sub_total": reduce(lambda total, item: total + (item.get('rate', 0) * item.get('quantity', 0)), io_logs, 0),
                    "discount": reduce(lambda total, item: total + item.get('discount_total', 0), io_logs, 0),
                    "round_discount": reduce(lambda total, item: total + item.get('round_discount', 0), io_logs, 0),
                    "orders": [order],
                    "group_id": group_code
                }
            )
        # CHeck if the delivery coupon available in order items
        health_os_helper = HealthOSHelper()
        delivery_coupon_stock_id = health_os_helper.get_delivery_coupon_stock_id()
        has_delivery_coupon = False
        for item in order_items:
            stock_id = item.get("stock").id
            if (str(stock_id) == str(delivery_coupon_stock_id)):
                has_delivery_coupon = True
                break
        return order_groups, has_delivery_coupon

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        custom_helper = CustomerHelper(request.user.organization_id)
        # Get org and area discount factor
        dynamic_discount_factor = custom_helper.get_organization_and_area_discount()
        org_discount_factor = dynamic_discount_factor.get("organization_discount_factor", 0.00)
        area_discount_factor = dynamic_discount_factor.get("area_discount_factor", 0.00)

        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
        DATE_FORMAT = '%Y-%m-%d'
        _datetime_now = datetime.strptime(
            time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
        _date_now = datetime.strptime(
            time.strftime(DATE_FORMAT, time.localtime()), DATE_FORMAT).date()
        system_platform = int(
            request.META.get("HTTP_X_SYSTEM_PLATFORM", SystemPlatforms.ECOM_WEB))
        app_version = request.headers.get('X-App-Version', '1.16.1')
        is_web = system_platform == SystemPlatforms.WEB_APP
        if (system_platform == SystemPlatforms.ANDROID_APP and app_version == "1.16.0") or (is_web and app_version >= "1.17.0"):
            cart_api_version = "V2"
        else:
            cart_api_version = "V1"
        geo_location_data = request.META.get("HTTP_GEODATA", "{}")
        healthos_settings = get_healthos_settings()
        order_groups = validated_data.pop('order_groups')
        distributor_order_groups, has_delivery_coupon = self.prepare_order_groups(
            validated_data, order_groups
        )
        group_grand_total = reduce(lambda total, item: total + item.get('sub_total', 0) - item.get('discount', 0) + item.get('round_discount', 0), distributor_order_groups, 0)

        express_delivery_stock_id = os.environ.get('EXPRESS_DELIVERY_STOCK_ID', None)
        min_order_amount = custom_helper.get_organization_data().min_order_amount
        # get minimum order amount for the ordered organization
        if express_delivery_stock_id is None:
            try:
                min_order_amount = Organization.objects.only('min_order_amount').get(
                    pk=request.user.organization_id
                ).min_order_amount
            except:
                min_order_amount = 0
            if group_grand_total < min_order_amount:
                raise serializers.ValidationError(
                    f"You minimum order amount is {min_order_amount}"
                )
        if not len(distributor_order_groups):
            raise serializers.ValidationError(
                "You may trying to place order with empty cart."
            )
        order_id_list = []
        user_allowed_to_place_order = False
        for _order_group_data in distributor_order_groups:
            orders = _order_group_data.pop('orders', [])
            order_group = DistributorOrderGroup.objects.create(
                order_type=DistributorOrderType.ORDER,
                organization_id=request.user.organization_id,
                entry_by_id=request.user.id,
                **_order_group_data
            )
            # Check if user allowed to place order
            for _order_data in orders:
                is_queueing_order_value = to_boolean(_order_data.get('is_queueing_order', False))
                delivery_date = get_tentative_delivery_date(
                    _order_data.get('purchase_date', _datetime_now),
                    is_queueing_order_value
                )
                order_can_be_placed = custom_helper.is_order_allowed(
                    delivery_date=delivery_date,
                    total_amount=group_grand_total
                )
                if order_can_be_placed is True:
                    user_allowed_to_place_order = True
            for order_data in orders:
                order_items = order_data.pop('stock_io_logs')
                order_data['purchase_date'] = _datetime_now
                is_queueing_order_value = to_boolean(order_data.get('is_queueing_order', False))

                # if system_platform == SystemPlatforms.ANDROID_APP and versiontuple(app_version) < versiontuple("1.17.0"):
                #     is_queueing_order_value = True
                order_data['tentative_delivery_date'] = get_tentative_delivery_date(
                    order_data.get('purchase_date', _datetime_now),
                    is_queueing_order_value
                )

                # Raise error if no delivery coupon available and not allowed to place order
                if not user_allowed_to_place_order and not has_delivery_coupon:
                    raise serializers.ValidationError(
                        f"Sorry insufficient amount to place order, order more then {min_order_amount}"
                    )

                order_data['geo_location_data'] = geo_location_data
                order_data['system_platform'] = system_platform
                order_data['is_queueing_order'] = is_queueing_order_value

                if not order_data.get('store_point', None):
                    try:
                        _store_point = healthos_settings.default_storepoint_id
                    except:
                        _store_point = None
                    order_data['store_point_id'] = _store_point
                tracking_status = OrderTrackingStatus.IN_QUEUE if is_queueing_order_value else OrderTrackingStatus.PENDING
                order_instance = Purchase.objects.create(
                    status=Status.DISTRIBUTOR_ORDER,
                    organization_id=request.user.organization_id,
                    distributor_order_type=DistributorOrderType.ORDER,
                    purchase_type=PurchaseType.VENDOR_ORDER,
                    distributor_order_group_id=order_group.id,
                    entry_by_id=request.user.id,
                    updated_by_id=request.user.id,
                    remarks=cart_api_version,
                    current_order_status=tracking_status,
                    customer_dynamic_discount_factor=org_discount_factor,
                    customer_area_dynamic_discount_factor=area_discount_factor,
                    **order_data
                )

                order_amount = 0
                order_discount = 0
                order_grand_total = 0
                order_round_discount = 0
                for item in reversed(order_items):
                    item['date'] = _date_now
                    primary_unit = item.get('primary_unit', None)
                    secondary_unit = item.get('secondary_unit', None)
                    # Set static value for unit
                    if not primary_unit:
                        # item['primary_unit_id'] = item.get('stock').product.primary_unit_id
                        item['primary_unit_id'] = 174
                    if not secondary_unit:
                        # item['secondary_unit_id'] = item.get('stock').product.secondary_unit_id
                        item['secondary_unit_id'] = 174
                    order_item = StockIOLog.objects.create(
                        purchase_id=order_instance.id,
                        status=order_instance.status,
                        organization_id=request.user.organization_id,
                        entry_by_id=request.user.id,
                        **item
                    )
                    # order_item.save()
                    order_amount += float(format(item.get('rate', 0) * item.get('quantity', 0), '.3f'))
                    order_discount += float(format(item.get('discount_total', 0), '.3f'))

                order_instance.amount = order_amount
                order_instance.discount = order_discount
                order_grand_total = order_amount - order_discount
                order_round_discount = float(format(round(order_grand_total) - order_grand_total, '.3f'))
                order_instance.round_discount = order_round_discount
                order_instance.grand_total = order_grand_total + order_round_discount
                order_instance.save()
                order_id_list.append(order_instance.id)

                # Create order tracking instance
                order_tracking = OrderTracking.objects.create(
                    order_status=tracking_status,
                    order_id=order_instance.id,
                    entry_by_id=request.user.id
                )
                # order_tracking.save()
                # Apply additional discount using celery
                # Creating an instance of CustomerHelper with the organization ID from the order_instance
                custom_helper = CustomerHelper(order_instance.organization_id)
                # Checking if the organization has a dynamic discount factor
                if not custom_helper.has_dynamic_discount_factor():
                    # If the organization doesn't have a dynamic discount factor, then apply additional discount
                    apply_additional_discount_on_order.apply_async(
                        (order_instance.id, group_grand_total, order_grand_total, is_queueing_order_value),
                        countdown=5,
                        retry=True, retry_policy={
                            'max_retries': 10,
                            'interval_start': 0,
                            'interval_step': 0.2,
                            'interval_max': 0.2,
                        }
                    )
        self.order_id_list = order_id_list

        return order_group


class DistributorOrderGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = DistributorOrderGroup
        fields = (
            'id',
            'alias',
            'sub_total',
            'discount',
        )


class DistributorOrderListGetSerializer(serializers.ModelSerializer):
    organization = OrganizationModelSerializer.LiteWithEntryBy(read_only=True)
    responsible_employee = PersonOrganizationEmployeeSearchSerializer()
    distributor_order_group = DistributorOrderGroupSerializer()
    prev_order_date = serializers.DateField()
    geo_location_data = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'grand_total',
            'calculated_profit',
            # 'person_organization_receiver',
            'transport',
            'tentative_delivery_date',
            'organization',
            'current_order_status',
            'organization',
            'responsible_employee',
            'prev_order_date',
            'order_number_count',
            "distributor_order_group",
            'system_platform',
            'geo_location_data',
            'is_queueing_order',
            'short_total',
            'return_total',
            'order_rating',
            'order_rating_comment',
            "additional_discount",
        )

    def get_geo_location_data(self, _obj):
        from elasticsearch_dsl import InnerDoc
        if isinstance(_obj.geo_location_data, InnerDoc):
            return _obj.geo_location_data.to_dict()
        return _obj.geo_location_data


class DistributorOrderListGetSerializerForUser(serializers.ModelSerializer):
    # distributor = OrganizationModelSerializer.Lite(read_only=True)
    # organization = OrganizationModelSerializer.LiteWithEntryBy(read_only=True)
    distributor_order_group = DistributorOrderGroupSerializer()
    # responsible_employee = PersonOrganizationEmployeeSearchSerializer()
    # prev_order_date = serializers.DateField()
    # geo_location_data = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            # 'receiver',
            # 'person_organization_receiver',
            # 'transport',
            'tentative_delivery_date',
            # 'distributor',
            # 'organization',
            'current_order_status',
            'distributor_order_group',
            # 'organization',
            # 'responsible_employee',
            # 'prev_order_date',
            # 'order_number_count',
            # 'system_platform',
            # 'geo_location_data',
            # 'is_queueing_order'
        )

    def get_geo_location_data(self, _obj):
        from elasticsearch_dsl import InnerDoc
        if isinstance(_obj.geo_location_data, InnerDoc):
            return _obj.geo_location_data.to_dict()
        return _obj.geo_location_data


class DistributorOrderDetailsGetForDistributorSerializer(serializers.ModelSerializer):
    distributor = OrganizationModelSerializer.Lite(read_only=True)
    organization = OrganizationModelSerializer.Lite(read_only=True)
    stock_io_logs = StockIOLogDetailsWithUnitDetailsSerializer(many=True)


    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'invoice_group',
            'distributor',
            'organization',
            'stock_io_logs',
            'additional_discount',
            'additional_discount_rate',
            'additional_cost',
            'additional_cost_rate',
            'tentative_delivery_date',
            'current_order_status',
            'order_rating',
            'order_rating_comment'
        )

class OrderStockIOForInvoiceGroupSerializer(serializers.ModelSerializer):
    stock_io_logs = StockIOLogDetailsWithUnitDetailsSerializer(many=True)


    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'grand_total',
            'stock_io_logs',
        )

class OrderStockIOForInvoiceGroupPDFSerializer(serializers.ModelSerializer):
    stock_io_logs = StockIOLogForInvoicePDFSerializer(many=True)


    class Meta:
        model = Purchase
        fields = (
            'id',
            'grand_total',
            'stock_io_logs',
        )


#pylint: disable=W0223
class DateAndStatusWiseOrderAmountSerializer(Serializer):
    purchase_date = serializers.DateField()
    tentative_delivery_date = serializers.DateField()
    current_order_status = serializers.IntegerField()
    amount_total = serializers.FloatField()
    discount_total = serializers.FloatField()
    number_of_orders = serializers.IntegerField()
    grand_total = serializers.FloatField()

class ResponsibleEmployeeWiseDeliverySheetSerializer(Serializer):
    order_ids = serializers.ListField()
    organization = serializers.SerializerMethodField()
    unique_item = serializers.IntegerField()
    total_item = serializers.IntegerField()
    order_count = serializers.IntegerField()
    order_amounts = serializers.SerializerMethodField()

    def get_organization(self, _obj):
        return construct_organization_object_from_dictionary(_obj)

    def get_order_amounts(self, _obj):
        from operator import itemgetter
        data = _obj.get('order_amounts', [])
        return sorted([dict(t) for t in {tuple(d.items()) for d in data}], key=itemgetter('id'))


class PurchaseRequisitionListGetSerializer(serializers.ModelSerializer):
    store_point = StorePointSerializer(fields=('alias', 'name'))
    person_organization_receiver = PersonOrganizationEmployeeSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    person_organization_supplier = PersonOrganizationLiteSerializer(
        read_only=True,
        allow_null=True,
        fields=('id', 'alias', 'company_name', 'first_name', 'last_name')
    )

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'vouchar_no',
            'purchase_date',
            'person_organization_receiver',
            'person_organization_supplier',
            'store_point',
            'amount',
            'transport',
            'grand_total',
            'organization_wise_serial',
            'department',
            'remarks',
        )


class DistributorOrderForShortReturnLogSerializer(serializers.ModelSerializer):
    responsible_employee = PersonOrganizationEmployeeSearchSerializer()

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'responsible_employee',
        )


class ReorderSerializer(Serializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        )
    )
    clear_cart = serializers.BooleanField(required=True)


class RequisitionRelatedOrderPurchaseLinkLiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'purchases',
        )


class RequisitionRelatedPurchaseOrderProcurementSerializer(serializers.ModelSerializer):
    procurements = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    orders = RequisitionRelatedOrderPurchaseLinkLiteSerializer(
        many=True
    )

    class Meta:
        model = Purchase
        fields = (
            'id',
            'alias',
            'procurements',
            'procure_group_requisitions',
            'orders',
        )


class DistributorOrderRatingSerializer(serializers.ModelSerializer):
    purchase_aliases = serializers.ListField(
        child=serializers.UUIDField(),
        allow_null=True, required=False, default=False, write_only=True
    )
    class Meta:
        model=Purchase
        fields=["purchase_aliases","order_rating", "order_rating_comment"]

    def validate(self, data):
        purchase_aliases = data.get("purchase_aliases")
        if not purchase_aliases:
            raise serializers.ValidationError("Must provide purchase aliases.")
        return data

    def create(self, validate_data):
        purchase_aliases = validate_data.pop("purchase_aliases", None)
        if purchase_aliases:
            # Convert the list of UUID strings to actual UUID objects
            uuid_objects = [str(alias) for alias in purchase_aliases]
            purchases = Purchase.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                alias__in=uuid_objects
            )

            # Get the updated values from validated_data
            order_rating = validate_data.get("order_rating", None)
            order_rating_comment = validate_data.get("order_rating_comment", None)

            # Bulk update the Purchase instances
            updates = []
            for purchase in purchases:
                purchase.order_rating = order_rating
                purchase.order_rating_comment = order_rating_comment
                updates.append(purchase)

            instance = Purchase.objects.bulk_update(updates, fields=["order_rating", "order_rating_comment"])

        return instance


class OrderPreOrderGraphListSerializer(serializers.Serializer):
    orders = serializers.IntegerField()
    pre_orders = serializers.IntegerField()
    date_time = serializers.DateTimeField()


class NonGroupedOrderSerializer(serializers.Serializer):
    organization=serializers.IntegerField()
    alias = serializers.UUIDField()
    name = serializers.CharField()
    orders = serializers.ListField(child=serializers.JSONField())
    total_amount = serializers.DecimalField(max_digits=19, decimal_places=3)
    total_discount = serializers.DecimalField(max_digits=19, decimal_places=3)
    grand_totals = serializers.DecimalField(max_digits=19, decimal_places=3)
