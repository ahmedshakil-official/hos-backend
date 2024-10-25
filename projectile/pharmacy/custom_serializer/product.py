'''
Move following serializer on this page:
<class 'pharmacy.serializers.ProductBasicSerializer'>
<class 'pharmacy.serializers.ProductWithoutStockSerializer'>
<class 'pharmacy.serializers.ProductWithStockSerializer'>
'''
from django.conf import settings
from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer
from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from pharmacy.serializers import (
    ProductFormSerializer,
    ProductManufacturingCompanySerializer
)
from pharmacy.models import Product
from pharmacy.custom_serializer.product_form import ProductFormModelSerializer
from pharmacy.custom_serializer.product_compartment import ProductCompartmentModelSerializer
from pharmacy.custom_serializer.product_generic import ProductGenericModelSerializer
from pharmacy.custom_serializer.product_manufacturing_company import ProductManufacturingCompanyModelSerializer
from ..enums import SystemPlatforms


class ProductMeta(ListSerializer.Meta):
    model = Product
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class ProductModelSerializer:
    class List(ListSerializer):

        from pharmacy.custom_serializer.product_manufacturing_company import ProductManufacturingCompanyModelSerializer
        from pharmacy.custom_serializer.product_form import ProductFormModelSerializer
        from pharmacy.custom_serializer.product_generic import ProductGenericModelSerializer
        from pharmacy.custom_serializer.product_subgroup import ProductSubgroupModelSerializer
        from pharmacy.custom_serializer.unit import UnitModelSerializer

        manufacturing_company = ProductManufacturingCompanyModelSerializer.Link()
        form = ProductFormModelSerializer.Link()
        subgroup = ProductSubgroupModelSerializer.List()
        generic = ProductGenericModelSerializer.Link()
        primary_unit = UnitModelSerializer.Link()
        secondary_unit = UnitModelSerializer.Link()
        image = VersatileImageFieldSerializer(
            sizes="product_images"
        )
        image_url = serializers.SerializerMethodField()

        class Meta(ProductMeta):
            fields = ListSerializer.Meta.fields + (
                'trading_price',
                'purchase_price',
                'manufacturing_company',
                'form',
                'subgroup',
                'generic',
                'is_salesable',
                'is_printable',
                'is_service',
                'primary_unit',
                'secondary_unit',
                'conversion_factor',
                'category',
                'code',
                'species',
                'name',
                'strength',
                'is_global',
                'image',
                'discount_rate',
                'order_limit_per_day',
                'image_url',
                'is_queueing_item',
            )

        def get_image_url(self, _object):
            path = f"{settings.FULL_MEDIA_URL}{_object.image}"
            return path if _object.image else None

    class StockDetails(List):
        '''
        This serializer will be used for stock details
        '''
        class Meta(ProductMeta):
            fields = ListSerializer.Meta.fields + (
                'trading_price',
                'purchase_price',
                'manufacturing_company',
                'form',
                'subgroup',
                'generic',
                'is_salesable',
                'is_printable',
                'is_service',
                'primary_unit',
                'secondary_unit',
                'conversion_factor',
                'category',
                'code',
                'species',
                'name',
                'strength',
                'is_global',
                'image',
                'discount_rate',
                'order_limit_per_day',
                'image_url',
                'is_queueing_item',
                'is_flash_item',
                # 'discount_rate_factor',
            )


    class Lite(ListSerializer):
        '''
        This serializer will be used for lite version of list
        '''
        class Meta(ProductMeta):
            fields = ProductMeta.fields + (
                'name',
                'strength',
                'status',
            )

    class SimplerList(ListSerializer):
        '''
        This serializer will be used for simpler list
        '''
        form = ProductFormSerializer()
        manufacturing_company = ProductManufacturingCompanySerializer()

        class Meta(ProductMeta):
            fields = ProductMeta.fields + (
                'name',
                'strength',
                'form',
                'manufacturing_company',
            )

    class InvoicePDF(ListSerializer):
        '''
        This serializer will be used for generating invoice group pdf
        '''
        form = ProductFormModelSerializer.NameOnly()
        compartment = ProductCompartmentModelSerializer.MinimalList()

        class Meta(ProductMeta):
            fields = ProductMeta.fields + (
                'name',
                'strength',
                'form',
                'compartment',
            )

    class ProductListFetchByStockId(ListSerializer):
        form_name = serializers.CharField(source="form.name", read_only=True)

        class Meta(ProductMeta):
            fields = ProductMeta.fields + (
                "name",
                "strength",
                "trading_price",
                "discount_rate",
                "form_name",
                "stock_list",
                "is_published",
                "is_flash_item",
                "is_salesable",
                "order_mode",
                "is_ad_enabled",
                "priority",
                "minimum_order_quantity",
            )


    class ECommerceProductSearch(ListSerializer):
        """
        This serializer will be used for E-Commerce Product Search
        """
        form = ProductFormModelSerializer.Link(read_only=True)
        manufacturing_company = ProductGenericModelSerializer.Link()
        generic = ProductGenericModelSerializer.Link()
        image = serializers.SerializerMethodField()

        class Meta(ProductMeta):
            fields = (
                "alias",
                "name",
                "strength",
                "full_name",
                "display_name",
                "form",
                "manufacturing_company",
                "generic",
                "order_mode",
                "is_published",
                "is_queueing_item",
                "is_salesable",
                "trading_price",
                "discount_rate",
                "order_limit_per_day",
                "image",
            )

        def get_image(self, _object):
            return _object.image.to_dict()
