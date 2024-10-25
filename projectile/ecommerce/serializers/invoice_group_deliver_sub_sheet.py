from django.db import transaction

from rest_framework import serializers

from ecommerce.enums import TopSheetType

from ecommerce.models import (
    InvoiceGroupDeliverySheet,
    DeliverySheetItem,
    DeliverySheetInvoiceGroup,
    TopSheetSubTopSheet,
)

from core.models import PersonOrganization

from common.enums import Status

from ecommerce.utils import (
    calculate_sub_top_sheet_total_data,
    assign_delivery_items_and_delivery_sheet_invoice_groups_to_sub_to_sheet,
    create_sub_top_sheet,
)


class SubSheetPostSerializer(serializers.Serializer):
    top_sheet = serializers.IntegerField(write_only=True)
    responsible_employee = serializers.CharField(write_only=True)

    order_by_organizations = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    def validate(self, attrs):
        top_sheet_id = attrs.get("top_sheet")
        responsible_employee_code = attrs.get("responsible_employee")

        # Validating top sheet and responsible employee alias
        if (
            top_sheet_id
            and not InvoiceGroupDeliverySheet().get_all_actives().filter(
                id=top_sheet_id,
            ).exists()
        ):
            raise serializers.ValidationError("Invalid top sheet id")

        if (
            responsible_employee_code
            and not PersonOrganization.objects.filter(
                status__in=[Status.ACTIVE, Status.DRAFT],
                code=responsible_employee_code,
            ).exists()
        ):
            raise serializers.ValidationError("Invalid responsible employee code")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        top_sheet_id = validated_data.get("top_sheet")
        responsible_employee_code = validated_data.get("responsible_employee")
        order_by_organizations = validated_data.get("order_by_organizations", [])

        top_sheet = InvoiceGroupDeliverySheet.objects.get(id=top_sheet_id)

        responsible_employee = PersonOrganization.objects.get(
            code=responsible_employee_code
        )
        # Create sub top sheet based on organization's primary responsible person
        if order_by_organizations:
            delivery_sheet_items = DeliverySheetItem().get_all_actives().filter(
                invoice_group_delivery_sheet__id=top_sheet_id,
                order_by_organization__alias__in=order_by_organizations,
            )
            error_message = "No delivery items found for the organizations"
        else:
            delivery_sheet_items = DeliverySheetItem().get_all_actives().filter(
                invoice_group_delivery_sheet__id=top_sheet_id,
                order_by_organization__primary_responsible_person__code=responsible_employee_code,
            )
            error_message = "No delivery items found for the responsible employee"

        if not delivery_sheet_items.exists():
            raise serializers.ValidationError(error_message)

        delivery_sheet_items_pk_list = delivery_sheet_items.values_list("pk", flat=True)

        #check if an existing sub top sheet existing for the responsible employee.
        existing_sub_top_sheet = InvoiceGroupDeliverySheet().get_all_actives().filter(
            type=TopSheetType.SUB_TOP_SHEET,
            responsible_employee_id=responsible_employee.id,
            sub_top_sheets__top_sheet_id=top_sheet.id,
            date=top_sheet.date,
        )

        if existing_sub_top_sheet.exists():
            sub_top_sheet = existing_sub_top_sheet.first()
        else:
            # Create top sub sheet
            sub_top_sheet = create_sub_top_sheet(top_sheet, responsible_employee)
            top_sheet_sub_top_sheet = TopSheetSubTopSheet.objects.create(
                top_sheet_id=top_sheet.id,
                sub_top_sheet_id=sub_top_sheet.id,
                organization_id=top_sheet.organization_id,
                entry_by_id=request.user.id,
            )

        # Assign delivery items and delivery sheet invoice groups to sub top sheet
        assign_delivery_items_and_delivery_sheet_invoice_groups_to_sub_to_sheet(
            delivery_sheet_items_pk_list,
            sub_top_sheet.id,
        )
        # if sub top sheet exists then calculation should be update on total delivery sheet items
        if existing_sub_top_sheet:
            delivery_sheet_items_pk_list = DeliverySheetItem().get_all_actives().filter(
                invoice_group_delivery_sub_sheet_id=sub_top_sheet.id,
            ).values_list("pk", flat=True)

        # calculate data for top sub sheet
        total_data = calculate_sub_top_sheet_total_data(
            delivery_sheet_items_pk_list,
        )

        sub_top_sheet.total_data = total_data
        sub_top_sheet.order_amount = total_data.get("total_order_amount")
        sub_top_sheet.short_amount = total_data.get("total_short_amount")
        sub_top_sheet.return_amount = total_data.get("total_return_amount")
        sub_top_sheet.save()

        return sub_top_sheet
