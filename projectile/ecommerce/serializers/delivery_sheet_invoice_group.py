from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from .order_invoice_group import OrderInvoiceGroupModelSerializer

from ..models import DeliverySheetInvoiceGroup


class DeliverySheetInvoiceGroupMeta(ListSerializer.Meta):
    model = DeliverySheetInvoiceGroup
    fields = ListSerializer.Meta.fields + (
        'date',
        'invoice_group',
        'sub_total',
        'grand_total',
        'discount',
        'round_discount',
        'additional_discount',
        'additional_cost',
        'total_short',
        'total_return',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class DeliverySheetInvoiceGroupModelSerializer:

    class Post(ListSerializer):

        class Meta(DeliverySheetInvoiceGroupMeta):
            fields = DeliverySheetInvoiceGroupMeta.fields + (

            )
            read_only_fields = DeliverySheetInvoiceGroupMeta.read_only_fields + ()

    class InvoiceGroupDeliverySheetDetails(ListSerializer):
        invoice_group = OrderInvoiceGroupModelSerializer.ForInvoiceGroupDeliverySheetDetails()

        class Meta(DeliverySheetInvoiceGroupMeta):
            fields = DeliverySheetInvoiceGroupMeta.fields + (
                # 'short_return_log',
            )
            read_only_fields = DeliverySheetInvoiceGroupMeta.read_only_fields + ()
