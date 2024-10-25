from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from core.custom_serializer.organization import OrganizationModelSerializer

from .delivery_sheet_invoice_group import DeliverySheetInvoiceGroupModelSerializer
from ..models import DeliverySheetItem


class DeliverySheetItemMeta(ListSerializer.Meta):
    model = DeliverySheetItem
    fields = ListSerializer.Meta.fields + (
        'date',
        'order_by_organization',
        'total_unique_item_order',
        'total_unique_item_short',
        'total_unique_item_return',
        'total_item_order',
        'total_item_short',
        'total_item_return',
        'order_count',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class DeliverySheetItemModelSerializer:

    class Post(ListSerializer):
        from ecommerce.serializers.delivery_sheet_invoice_group import DeliverySheetInvoiceGroupModelSerializer

        delivery_sheet_invoice_groups = DeliverySheetInvoiceGroupModelSerializer.Post(many=True)

        class Meta(DeliverySheetItemMeta):
            fields = DeliverySheetItemMeta.fields + (
                'delivery_sheet_invoice_groups',
            )
            read_only_fields = DeliverySheetItemMeta.read_only_fields + ()

    class InvoiceGroupDeliverySheetDetails(ListSerializer):
        order_by_organization = OrganizationModelSerializer.LiteWithGeoLocation()
        delivery_sheet_invoice_groups = DeliverySheetInvoiceGroupModelSerializer.InvoiceGroupDeliverySheetDetails(many=True)

        class Meta(DeliverySheetItemMeta):
            fields = DeliverySheetItemMeta.fields + (
                'delivery_sheet_invoice_groups',
            )
            read_only_fields = DeliverySheetItemMeta.read_only_fields + ()


    class DeliverySheetItemSerializerWithPorterAndInvoiceAssignee(InvoiceGroupDeliverySheetDetails):
        from core.serializers import PersonOrganizationEmployeeSearchSerializer

        is_assigned = serializers.CharField(max_length=250,read_only=True)
        order_by_organization = OrganizationModelSerializer.LiteWithResponsiblePerson()
        responsible_employee = PersonOrganizationEmployeeSearchSerializer(source='invoice_group_delivery_sub_sheet.responsible_employee')
        class Meta(DeliverySheetItemMeta):
            fields = DeliverySheetItemMeta.fields + (
                'responsible_employee',
                'is_assigned'
            )
            read_only_fields = DeliverySheetItemMeta.read_only_fields + ()

    class DeliverySheetItemSerializerWithPorterAndInvoice(InvoiceGroupDeliverySheetDetails):
        from core.serializers import PersonOrganizationEmployeeSearchSerializer

        is_assigned = serializers.CharField(max_length=250,read_only=True)
        order_by_organization = OrganizationModelSerializer.LiteWithResponsiblePerson()
        responsible_employee = PersonOrganizationEmployeeSearchSerializer(source='invoice_group_delivery_sheet.responsible_employee')
        class Meta(DeliverySheetItemMeta):
            fields = DeliverySheetItemMeta.fields + (
                'responsible_employee',
                'is_assigned',
            )
            read_only_fields = DeliverySheetItemMeta.read_only_fields + ()
