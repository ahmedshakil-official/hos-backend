from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status

from ..models import ProcureItem
from .prediction_item import PredictionItemModelSerializer


class TimeField(serializers.Field):
    def to_representation(self, value):
        days = value.days
        hours, remainder = divmod(value.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days} days {hours:02d}:{minutes:02d}:{seconds:02d}"


class ProcureItemMeta(ListSerializer.Meta):
    model = ProcureItem
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'date',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProcureItemModelSerializer:

    class List(ListSerializer):

        class Meta(ProcureItemMeta):
            fields = ProcureItemMeta.fields + (

            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()

    class ProductWiseReport(ListSerializer):
        from procurement.serializers.procure_proxy import ProcureModelProxySerializer

        procure = ProcureModelProxySerializer.ProductWiseReport()
        prediction_item = PredictionItemModelSerializer.ProductWiseReport()

        class Meta(ProcureItemMeta):
            fields = ProcureItemMeta.fields + (
                'quantity',
                'rate',
                'procure',
                'rate_status',
                'product_name',
                'prediction_item',
                'stock',
                'company_name',
            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()


    class Post(ListSerializer):

        def validate(self, data):
            from pharmacy.helpers import get_product_short_name

            request = self.context.get("request")
            copied_from = request.data.get("copied_from", None)
            quantity = data.get("quantity", 0)
            stock = data.get("stock", "")
            prediction_item = data.get("prediction_item", "")
            product_full_name = get_product_short_name(stock.product)
            is_valid_quantity = quantity + prediction_item.purchase_order <= prediction_item.suggested_purchase_quantity
            valid_quantity = prediction_item.suggested_purchase_quantity - prediction_item.purchase_order
            valid_worst_rate = prediction_item.worst_rate
            rate = data.get("rate", 0)
            if request.user.is_admin_or_super_admin_or_procurement_manager_or_procurement_coordinator() and valid_worst_rate == 0 and rate >= valid_worst_rate:
                pass
            elif rate > valid_worst_rate:
                raise serializers.ValidationError({
                    'rate': _(f"Purchase rate can't be greater than suggested rate for {product_full_name}. It must be less or equal {round(valid_worst_rate, 2)}"),
                    'stock_id': stock.id if stock else ""
                })
            # Over purchase permission validation
            if request.user.has_permission_for_procurement_over_purchase():
                return data

            if copied_from:
                prev_procure_item = ProcureItem.objects.only('quantity').filter(
                    status=Status.ACTIVE,
                    procure__id=copied_from,
                    stock=stock,
                    prediction_item=prediction_item
                ).first()
                prev_quantity = prev_procure_item.quantity if prev_procure_item else 0
                is_valid_quantity = quantity + prediction_item.purchase_order - prev_quantity <= prediction_item.suggested_purchase_quantity
                valid_quantity = prediction_item.suggested_purchase_quantity - prediction_item.purchase_order + prev_quantity
            if not is_valid_quantity:
                raise serializers.ValidationError({
                    'quantity': _(f"Purchase quantity can't be greater than suggested quantity for {product_full_name}. It must be less or equal {round(valid_quantity, 2)}"),
                    'stock_id': stock.id if stock else ""
                })
            return data

        class Meta(ProcureItemMeta):
            fields = ProcureItemMeta.fields + (
                'stock',
                'prediction_item',
                'rate',
                'quantity',
                'rate_status',
                'company_name',
            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()

    class Details(ListSerializer):
        prediction_item = PredictionItemModelSerializer.ProcureDetailsGet()

        class Meta(ProcureItemMeta):
            fields = ProcureItemMeta.fields + (
                'stock',
                'prediction_item',
                'rate',
                'quantity',
                'rate_status',
                'company_name',
                'product_name',
            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()

    class StockWithQuantityAndRate(ListSerializer):
        class Meta(ProcureItemMeta):
            fields = (
                'stock',
                'quantity',
                'rate'
            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()

    class Lite(ListSerializer):
        prediction_item = PredictionItemModelSerializer.CompanyNameWithMrp(read_only=True)

        class Meta(ProcureItemMeta):
            fields = (
                'id',
                'quantity',
                'rate',
                'rate_status',
                'product_name',
                'stock',
                'prediction_item',
            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()

    class DateWisePurchaseReport(ListSerializer):
        ID = serializers.IntegerField(source='stock.id')
        supplier_company_name = serializers.CharField(source='procure.supplier.company_name')
        pur = serializers.CharField(source='rate')
        by = serializers.CharField(source='BY')
        sales = serializers.DecimalField(source='prediction_item.sale_price', max_digits=19, decimal_places=3)
        best_rate = serializers.DecimalField(source='prediction_item.avg_purchase_rate', max_digits=19, decimal_places=3)
        worst_rate = serializers.DecimalField(source='prediction_item.worst_rate', max_digits=19, decimal_places=3)
        procure_operation_start = serializers.DateTimeField(source='procure.operation_start')
        procure_operation_end = serializers.DateTimeField(source='procure.operation_end')
        pre_pur = serializers.DecimalField(source='prediction_item.real_avg', max_digits=19, decimal_places=3)
        prediction_item_lowest_purchase_rate = serializers.DecimalField(source='prediction_item.lowest_purchase_rate', max_digits=19, decimal_places=3)
        d3 = serializers.DecimalField(source='prediction_item.suggested_purchase_quantity', max_digits=19, decimal_places=3)
        d1 = serializers.DecimalField(source='prediction_item.suggested_min_purchase_quantity', max_digits=19, decimal_places=3)
        profit = serializers.DecimalField(source='PROFIT', max_digits=19, decimal_places=3)
        delta = serializers.DecimalField(source='DELTA', max_digits=19, decimal_places=3)
        total_profit = serializers.SerializerMethodField()
        pur_val = serializers.DecimalField(source='PUR_VAL', max_digits=19, decimal_places=3)
        time = TimeField(source='TIME')
        sales_val = serializers.DecimalField(source='SALES_VAL', max_digits=19, decimal_places=3)

        def get_total_profit(self, obj):
            return obj.PROFIT * obj.quantity

        class Meta(ProcureItemMeta):
            fields = ProcureItemMeta.fields + (
                'ID',
                'procure',
                'supplier_company_name',
                'product_name',
                'company_name',
                'pur',
                'quantity',
                'sales',
                'best_rate',
                'worst_rate',
                'procure_operation_start',
                'procure_operation_end',
                'pre_pur',
                'prediction_item_lowest_purchase_rate',
                'd3',
                'd1',
                'by',
                'profit',
                'delta',
                'total_profit',
                'pur_val',
                'time',
                'sales_val',
            )
            read_only_fields = ProcureItemMeta.read_only_fields + ()
