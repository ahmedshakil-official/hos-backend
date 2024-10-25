
from rest_framework import serializers
from rest_framework.serializers import (
    ModelSerializer,
)
from pharmacy.serializers import (
    UnitSerializer, StorePointSerializer,
)
from pharmacy.custom_serializer.product import ProductModelSerializer
from pharmacy.models import Stock



class SalesableProductOrServiceSerializer(ModelSerializer):
    log_price = serializers.FloatField(default=0.0)
    latest_purchase_unit = UnitSerializer()
    latest_sale_unit = UnitSerializer()
    store_point = StorePointSerializer()
    product = ProductModelSerializer.List()
    stock = serializers.FloatField(min_value=0)

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'store_point',
            'product',
            'stock',
            'demand',
            'auto_adjustment',
            'minimum_stock',
            'rack',
            'tracked',
            'tracked',
            'sales_rate',
            'purchase_rate',
            'calculated_price',
            'order_rate',
            'log_price',
            'latest_purchase_unit',
            'latest_sale_unit',
            'discount_margin',
        )

class StockProductCachedListSerializer(SalesableProductOrServiceSerializer):
    sales_log_price = serializers.FloatField(default=0.0)
    purchase_log_price = serializers.FloatField(default=0.0)

    # pylint: disable=old-style-class, no-init
    class Meta(SalesableProductOrServiceSerializer.Meta):
        fields = SalesableProductOrServiceSerializer.Meta.fields + (
            'sales_log_price',
            'purchase_log_price'
        )

class StockProductNonCachedListSerializer(SalesableProductOrServiceSerializer):
    log_price = serializers.SerializerMethodField()

    def get_log_price(self, _obj):
        if self.context.get('sales_able'):
            return _obj.sales_log_price
        return _obj.purchase_log_price
