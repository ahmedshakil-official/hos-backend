from rest_framework import serializers
from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from core.custom_serializer.organization import OrganizationModelSerializer
from ..models import Stock
from ..serializers import (
    StorePointSerializer,
    ProductWithoutUnitSerializer,
    ProductSerializer,
    UnitSerializer,
)
from ..custom_serializer.product import ProductModelSerializer


class StockMeta(ListSerializer.Meta):
    model = Stock
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProductShortReportSerializer:

    class List(ListSerializer):
        store_point = StorePointSerializer()
        product = ProductWithoutUnitSerializer()
        sale_qty = serializers.IntegerField()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                'minimum_stock',
                'product',
                'store_point',
                'sale_qty',
            )
            read_only_fields = StockMeta.read_only_fields + (
                'sale_qty',
            )

    class Details(ListSerializer):
        store_point = StorePointSerializer()
        product = ProductSerializer()
        latest_purchase_unit = UnitSerializer()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                'minimum_stock',
                'product',
                'store_point',
                'latest_purchase_unit',
            )


class StockReportDemandSerializer:

    class List(ListSerializer):
        store_point = StorePointSerializer()
        product = ProductWithoutUnitSerializer()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                'minimum_stock',
                'product',
                'store_point',
                'calculated_price',
                'demand',
                'auto_adjustment',
                'purchase_rate',
            )


class StoreWiseStockValueSerializer:
    class List(ListSerializer):
        product_group = serializers.IntegerField()
        group_name = serializers.CharField()
        stock_value = serializers.FloatField()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock_value',
                'product_group',
                'group_name'
            )

class DistributorSalesableStock:

    class ListForGeneralUser(ListSerializer):
        product = ProductModelSerializer.List()
        # organization = OrganizationModelSerializer.Lite()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                'product',
                # 'organization',
                'store_point',
                'orderable_stock',
            )

    class ListForSuperAdmin(ListForGeneralUser):
        # store_point = StorePointSerializer()
        product = ProductModelSerializer.List()
        # organization = OrganizationModelSerializer.LiteForDistributorStockProductList()
        is_out_of_stock = serializers.BooleanField()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                'product',
                # 'organization',
                'store_point',
                'orderable_stock',
                'is_out_of_stock',
                'delivery_date',
                # 'avg_purchase_rate_today',
                # 'avg_purchase_rate_yesterday',
                # 'avg_purchase_rate_last_3_days',
                # 'avg_purchase_rate_last_7_days',
                # 'avg_purchase_rate_last_15_days',
                # 'avg_purchase_rate_last_30_days',
                # 'avg_purchase_rate_days',
            )

    class Details(ListSerializer):
        product = ProductModelSerializer.StockDetails()
        organization = OrganizationModelSerializer.LiteForDistributorStockProductList()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                'product',
                'organization',
                'store_point',
                'orderable_stock',
                'is_limited_stock',
                'is_trending',
                'is_out_of_stock',
                'delivery_date',
                'is_order_enabled',
            )


class ProductWiseDistributorOrderDiscountSummarySerializer(serializers.Serializer):
    product_full_name = serializers.CharField()
    id = serializers.IntegerField()
    order_date = serializers.DateField()
    number_of_order = serializers.IntegerField()
    discount = serializers.IntegerField()
    quantity = serializers.IntegerField()


class MismatchedStockWithIOSerializer:

    class List(ListSerializer):
        # product = ProductWithoutUnitSerializer()
        # organization = OrganizationModelSerializer.Lite()
        # store_point = StorePointSerializer(
        #     fields=('alias', 'name')
        # )
        current_stock = serializers.IntegerField()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                'stock',
                # 'product',
                # 'organization',
                # 'store_point',
                'current_stock',
            )
            read_only_fields = StockMeta.read_only_fields + (
                'current_stock',
            )

class StockWithProductUnitForCartV2Serializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'store_point',
            'product',
        )


class StockSearchBaseSerializer:

    class ECommerceStockProductSearch(ListSerializer):
        product = ProductModelSerializer.ECommerceProductSearch()

        class Meta(StockMeta):
            fields = ListSerializer.Meta.fields + (
                "id",
                "alias",
                "store_point",
                "product",
                "is_order_enabled",
                "is_out_of_stock",
                "delivery_date",
            )
            read_only_fields = StockMeta.read_only_fields + (

            )


class StockForCartGetSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Stock
        fields = (
            'id',
            'alias',
            'product',
            'is_delivery_coupon',
        )


class StockForInvoicePDFSerializer(serializers.ModelSerializer):
    product = ProductModelSerializer.InvoicePDF()

    class Meta:
        model = Stock
        fields = (
            'id',
            'product',
        )
