from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from ecommerce.models import InvoiceGroupPdf

class InvoiceGroupPdfMeta(ListSerializer.Meta):
    model = InvoiceGroupPdf
    fields = ListSerializer.Meta.fields + (
        "content",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class InvoiceGroupPdfModelSerializer:
    class List(ListSerializer):

        class Meta(InvoiceGroupPdfMeta):
            fields = InvoiceGroupPdfMeta.fields + (
                "status",
                "name",
                "invoice_group",
                "created_at"
            )
