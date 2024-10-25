
from rest_framework import serializers
from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from ecommerce.models import InvoicePdfGroup

class InvoicePdfGroupMeta(ListSerializer.Meta):
    model = InvoicePdfGroup
    fields = ListSerializer.Meta.fields + (
        "content",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class InvoicePdfGroupModelSerializer:

    class Post(serializers.Serializer):
        delivery_date = serializers.DateField()

        class Meta(InvoicePdfGroupMeta):
            fields = (
                "delivery_date",
            )

    class List(ListSerializer):

        class Meta(InvoicePdfGroupMeta):
            fields = InvoicePdfGroupMeta.fields + (
                "status",
                "name",
                "delivery_date",
                "download_count",
                "invoice_count",
                "page_count",
                "repeat",
                "invoice_groups",
                "area",
                "created_at"
            )


    class Details(ListSerializer):

        class Meta(InvoicePdfGroupMeta):
            fields = InvoicePdfGroupMeta.fields + (
                "status",
                "name",
                "delivery_date",
                "download_count",
                "invoice_count",
                "page_count",
                "repeat",
                "invoice_groups",
                "created_at"
            )
