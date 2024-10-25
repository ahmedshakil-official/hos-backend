from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from .prediction_item_supplier import PredictionItemSupplierModelSerializer
from ..models import PredictionItem

class PredictionItemMeta(ListSerializer.Meta):
    model = PredictionItem
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'date',
        'stock',
        'mrp',
        'sale_price',
        'avg_purchase_rate',
        'lowest_purchase_rate',
        'highest_purchase_rate',
        'margin',
        'suggested_purchase_quantity',
        'purchase_order',
        'purchase_quantity',
        'product_name',
        'company_name',
        'marked_status',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class PredictionItemModelSerializer:

    class List(ListSerializer):
        prediction_item_suggestions = PredictionItemSupplierModelSerializer.List(many=True)
        # supplier_avg_rate = serializers.SerializerMethodField()

        class Meta(PredictionItemMeta):
            fields = PredictionItemMeta.fields + (
                'prediction_item_suggestions',
                'suggested_min_purchase_quantity',
                'has_min_purchase_quantity',
                'real_avg',
                'worst_rate',
                # 'supplier_avg_rate',
            )
            read_only_fields = PredictionItemMeta.read_only_fields + ()

        def get_supplier_avg_rate(self, obj):
            request = self.context.get('request')
            supplier_alias = request.query_params.get('supplier', '')
            return obj.get_supplier_avg_rate(supplier_alias)

    class ProcureDetailsGet(ListSerializer):

        class Meta(PredictionItemMeta):
            fields = PredictionItemMeta.fields + (

            )
            read_only_fields = PredictionItemMeta.read_only_fields + ()

    class Lite(ListSerializer):

        class Meta(PredictionItemMeta):
            fields = (
                'avg_purchase_rate',
                'sale_price',
                'date',
                'product_name',
                'company_name',
            )
            read_only_fields = PredictionItemMeta.read_only_fields + ()

    class ProductWiseReport(ListSerializer):

        class Meta(PredictionItemMeta):
            fields = (
                'avg_purchase_rate',
            )
            read_only_fields = PredictionItemMeta.read_only_fields + ()

    class WithWorstRate(ListSerializer):
        class Meta(PredictionItemMeta):
            fields = PredictionItemMeta.fields + (
                'worst_rate',
            )
            read_only_fields = PredictionItemMeta.read_only_fields + ()

    class CompanyNameWithMrp(ListSerializer):
        class Meta(PredictionItemMeta):
            fields = (
                'company_name',
                'mrp',
            )
            read_only_fields = PredictionItemMeta.read_only_fields + ()
