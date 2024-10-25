import json
import time
from datetime import datetime

from django.db import transaction
from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status
from common.validators import (
    validate_unique_name
)
from core.models import PersonOrganization

from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.custom_serializer.organization import OrganizationModelSerializer
from core.custom_serializer.person_organization import (
    PersonOrganizationModelSerializer,
)

from ..models import InvoiceGroupDeliverySheet, DeliverySheetItem, DeliverySheetInvoiceGroup


class InvoiceGroupDeliverySheetMeta(ListSerializer.Meta):
    model = InvoiceGroupDeliverySheet
    fields = ListSerializer.Meta.fields + (
        'name',
        'date',
        'responsible_employee',
        'generated_by',
        'query_params',
        'filter_data',
        "type",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class InvoiceGroupDeliverySheetModelSerializer:

    class Post(ListSerializer):
        from ecommerce.serializers.delivery_sheet_item import DeliverySheetItemModelSerializer

        delivery_sheet_items = DeliverySheetItemModelSerializer.Post(many=True)

        order_amount = serializers.DecimalField(required=False, max_digits=19, decimal_places=3)
        short_amount = serializers.DecimalField(required=False, max_digits=19, decimal_places=3)
        return_amount = serializers.DecimalField(required=False, max_digits=19, decimal_places=3)
        coordinator = serializers.SlugRelatedField(
            queryset=PersonOrganization().get_all_non_inactives(),
            slug_field="alias",
            error_messages={
                "detail": "Coordinator does not exist.",
            },
            required=True
        )

        class Meta(InvoiceGroupDeliverySheetMeta):
            fields = InvoiceGroupDeliverySheetMeta.fields + (
                'delivery_sheet_items',
                'total_data',
                'order_amount',
                'short_amount',
                'return_amount',
                'coordinator',
            )
            read_only_fields = InvoiceGroupDeliverySheetMeta.read_only_fields + ()

        # def validate_name(self, value):

        #     if validate_unique_name(self, value, InvoiceGroupDeliverySheet):
        #         return value
        #     else:
        #         message = f"You already have a top sheet with same name, please delete it first."
        #         raise serializers.ValidationError(message)

        @transaction.atomic
        def create(self, validated_data):
            order_amount = validated_data.get('order_amount', None)
            short_amount = validated_data.get('short_amount', None)
            return_amount = validated_data.get('return_amount', None)
            # Assuming validated_data['total_data'] is a JSON string
            total_data_str = validated_data.get('total_data', None)

            request = self.context.get("request")
            DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
            _datetime_now = datetime.strptime(
                time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
            delivery_sheet_items = validated_data.pop('delivery_sheet_items', [])
            validated_data['date'] = _datetime_now
            responsible_employee = validated_data.get('responsible_employee')
            coordinator = validated_data.get('coordinator')

            # Now that we are receiving the coordinator from the front-end,
            # we directly update the coordinator in the responsible employee's manager field.
            responsible_employee.manager = coordinator
            responsible_employee.save()

            # try:
            #     responsible_employee = validated_data.get('responsible_employee')
            #     manager = responsible_employee.manager
            # except:
            #     manager = None
            #
            # # Show error if the delivery man have no manager/coordinator
            # if not manager:
            #     raise serializers.ValidationError({
            #         "error": "The selected responsible employee has no manager, Please assign a manager and submit again."
            #     })

            invoice_group_delivery_sheet = InvoiceGroupDeliverySheet.objects.create(
                **validated_data
            )

            try:
                total_data_dict = json.loads(total_data_str)

                # Now we can access the values as a dictionary
                total_order_amount = total_data_dict.get('total_order_amount')
                total_short_amount = total_data_dict.get('total_short_amount')
                total_return_amount = total_data_dict.get('total_return_amount')

                if order_amount is None and total_order_amount is not None:
                    invoice_group_delivery_sheet.order_amount = int(total_order_amount)
                if short_amount is None and total_short_amount is not None:
                    invoice_group_delivery_sheet.short_amount = int(total_short_amount)
                if return_amount is None and total_return_amount is not None:
                    invoice_group_delivery_sheet.return_amount = int(total_return_amount)

                # Save the changes to the object
                invoice_group_delivery_sheet.save()

            except json.JSONDecodeError:
                raise ValueError("Error parsing JSON data in validated_data['total_data']")

            for item in delivery_sheet_items:
                delivery_sheet_invoice_groups = item.pop('delivery_sheet_invoice_groups', [])
                item['invoice_group_delivery_sheet'] = invoice_group_delivery_sheet
                item['organization_id'] = request.user.organization_id
                item['entry_by_id'] = request.user.id
                delivery_sheet_item = DeliverySheetItem.objects.create(
                    **item
                )
                for delivery_sheet_invoice_group in delivery_sheet_invoice_groups:
                    delivery_sheet_invoice_group['delivery_sheet_item'] = delivery_sheet_item
                    delivery_sheet_invoice_group['organization_id'] = request.user.organization_id
                    delivery_sheet_invoice_group['entry_by_id'] = request.user.id
                    delivery_sheet_invoice_group = DeliverySheetInvoiceGroup.objects.create(
                        **delivery_sheet_invoice_group
                    )

            return invoice_group_delivery_sheet

    class List(ListSerializer):
        generated_by = PersonOrganizationEmployeeSearchSerializer()
        responsible_employee = PersonOrganizationEmployeeSearchSerializer()
        coordinator = PersonOrganizationModelSerializer.MinimalList()
        filter_data = serializers.JSONField()
        total_data = serializers.JSONField()

        class Meta(InvoiceGroupDeliverySheetMeta):
            fields = InvoiceGroupDeliverySheetMeta.fields + (
                'filter_data',
                'coordinator',
                'total_data',
            )
            read_only_fields = InvoiceGroupDeliverySheetMeta.read_only_fields + ()

    class Details(ListSerializer):
        from ecommerce.serializers.delivery_sheet_item import DeliverySheetItemModelSerializer

        delivery_sheet_items = DeliverySheetItemModelSerializer.InvoiceGroupDeliverySheetDetails(many=True)
        sub_top_sheet_delivery_sheet_items = DeliverySheetItemModelSerializer.InvoiceGroupDeliverySheetDetails(many=True)
        filter_data = serializers.JSONField()
        query_params = serializers.JSONField()
        total_data = serializers.JSONField()
        coordinator = PersonOrganizationModelSerializer.MinimalList()

        def to_representation(self, instance):
            data = super().to_representation(instance)
            sub_top_sheet_delivery_sheet_items = data.pop("sub_top_sheet_delivery_sheet_items", [])
            if sub_top_sheet_delivery_sheet_items:
                data["delivery_sheet_items"] = sub_top_sheet_delivery_sheet_items
            return data

        class Meta(InvoiceGroupDeliverySheetMeta):
            fields = InvoiceGroupDeliverySheetMeta.fields + (
                'delivery_sheet_items',
                'sub_top_sheet_delivery_sheet_items',
                'total_data',
                'status',
                'coordinator',
                'is_short_return_amount_mismatched',
            )
            read_only_fields = InvoiceGroupDeliverySheetMeta.read_only_fields + ()

    class Info(ListSerializer):
        class Meta(InvoiceGroupDeliverySheetMeta):
            fields = (
                'id',
                'info',
            )
            read_only_fields = InvoiceGroupDeliverySheetMeta.read_only_fields + ()

