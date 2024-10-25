from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from core.custom_serializer.person import PersonModelSerializer
from pharmacy.models import ProductChangesLogs


# pylint: disable=old-style-class, no-init
class ProductChangesLogsMeta(ListSerializer.Meta):
    model = ProductChangesLogs

    fields = ListSerializer.Meta.fields + (
        'created_at',
        'updated_by',
        'updated_at',
        'name',
        'strength',
        'generic',
        'form',
        'manufacturing_company',
        'trading_price',
        'purchase_price',
        'order_limit_per_day',
        'order_limit_per_day_mirpur',
        'order_limit_per_day_uttara',
        'is_published',
        'discount_rate',
        'order_mode',
        'is_flash_item',
        'unit_type',
        'compartment',
        'is_queueing_item',
        'is_salesable'
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (

    )


class ProductChangesLogsModelSerializer:
    class List(ListSerializer):
        entry_by = PersonModelSerializer.EntryBy(read_only=True)
        product_name = serializers.CharField(source='product.name')
        name = serializers.JSONField()
        strength = serializers.JSONField()
        generic = serializers.JSONField()
        form = serializers.JSONField()
        manufacturing_company = serializers.JSONField()
        trading_price = serializers.JSONField()
        purchase_price = serializers.JSONField()
        order_limit_per_day = serializers.JSONField()
        is_published = serializers.JSONField()
        discount_rate = serializers.JSONField()
        order_mode = serializers.JSONField()
        is_flash_item = serializers.JSONField()
        unit_type = serializers.JSONField()
        compartment = serializers.JSONField()
        is_queueing_item = serializers.JSONField()
        is_salesable = serializers.JSONField()

        class Meta(ProductChangesLogsMeta):
            fields = ProductChangesLogsMeta.fields + (
                'product',
                'product_name',
                'entry_by',
                'date',
            )
            read_only_fields = ProductChangesLogsMeta.read_only_fields + (

            )

    class Details(ListSerializer):
        class Meta(ProductChangesLogsMeta):
            fields = ProductChangesLogsMeta.fields + (

            )
            read_only_fields = ProductChangesLogsMeta.read_only_fields + (

            )
