from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.custom_serializer.organization import OrganizationModelSerializer

from ..models import StockDelivery


class StockDeliveryMeta(ListSerializer.Meta):
    model = StockDelivery
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class StockDeliveryModelSerializer:

    class Details(ListSerializer):

        class Meta(StockDeliveryMeta):
            fields = ListSerializer.Meta.fields + (
                'id',
                'alias',
                'product_name',
                'tracking_status',
                'quantity',
                'rate',
                'date',
                'unit',
                'discount_rate',
                'discount_total',
                'vat_rate',
                'vat_total',
                'tax_total',
                'tax_rate',
            )
            read_only_fields = StockDeliveryMeta.read_only_fields + ()

    class StatusUpdate(ListSerializer):

        class Meta(StockDeliveryMeta):
            fields = ListSerializer.Meta.fields + (
                'tracking_status',
                'quantity',
            )
            read_only_fields = StockDeliveryMeta.read_only_fields + ()
