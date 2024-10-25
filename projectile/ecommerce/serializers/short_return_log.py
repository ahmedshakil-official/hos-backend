import datetime
from django.db import transaction
from rest_framework import serializers

from common.exception_handler import ValidationError
from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status

from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.custom_serializer.organization import OrganizationModelSerializer
from core.custom_serializer.person_organization import PersonOrganizationModelSerializer
from core.models import PersonOrganization

from .short_return_item import ShortReturnItemModelSerializer
from ..models import ShortReturnLog, ShortReturnItem, InvoiceGroupDeliverySheet


class ShortReturnLogMeta(ListSerializer.Meta):
    model = ShortReturnLog
    fields = ListSerializer.Meta.fields + (
        'date',
        'received_by',
        'order_by_organization',
        'order',
        'invoice_group',
        'order_amount',
        'short_return_amount',
        'total_order_items',
        'total_order_unique_items',
        'total_short_return_items',
        'total_short_return_unique_items',
        'type',
        'round_discount',
        'remarks',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ShortReturnLogModelSerializer:

    class Post(ListSerializer):
        from ecommerce.serializers.short_return_item import ShortReturnItemModelSerializer
        short_return_items = ShortReturnItemModelSerializer.Post(many=True)

        class Meta(ShortReturnLogMeta):
            fields = ShortReturnLogMeta.fields + (
                'status',
                'short_return_items',
            )
            read_only_fields = ShortReturnLogMeta.read_only_fields + ()

        def validate_invoice_group(self, invoice_group):
            date = self.context.get("request").data[0]["date"]
            received_by = self.context.get("request").data[0]["received_by"]
            short_return_log = ShortReturnLog.objects.filter(
                date=date,
                invoice_group=invoice_group,
                received_by__id=received_by,
            ).values_list('id', flat=True)
            if short_return_log.exists():
                raise ValidationError(
                    f'Short Return Log already exists [ID: #{short_return_log[0]}]. '
                    f'Multiple Submission is not allowed')
            return invoice_group

        @transaction.atomic
        def create(self, validated_data):
            request = self.context.get("request")
            short_return_items = validated_data.pop('short_return_items')
            _status = validated_data.get('status', Status.ACTIVE)
            referer = request.META.get('HTTP_APPLICATION', None)
            if referer is None:
                validated_data['approved_by'] = validated_data.get('received_by')
                validated_data['approved_at'] = datetime.datetime.now()
            short_return_log = ShortReturnLog.objects.create(
                **validated_data
            )
            # short_return_log.save()
            for item in short_return_items:
                item['short_return_log'] = short_return_log
                item['organization_id'] = request.user.organization_id
                item['entry_by_id'] = request.user.id
                item['status'] = _status
                short_return_item = ShortReturnItem.objects.create(
                    **item
                )
                # short_return_item.save()

            return short_return_log

    class List(ListSerializer):
        received_by = PersonOrganizationEmployeeSearchSerializer()
        order_by_organization = OrganizationModelSerializer.Lite()
        approved_by = PersonOrganizationModelSerializer.MinimalList()

        class Meta(ShortReturnLogMeta):
            fields = ShortReturnLogMeta.fields + (
                'status',
                'approved_by',
                'approved_at',
            )
            read_only_fields = ShortReturnLogMeta.read_only_fields + ()

    class Lite(ListSerializer):

        class Meta(ShortReturnLogMeta):
            fields = ShortReturnLogMeta.fields + (

            )
            read_only_fields = ShortReturnLogMeta.read_only_fields + ()

    class Details(ListSerializer):
        received_by = PersonOrganizationEmployeeSearchSerializer()
        approved_by = PersonOrganizationEmployeeSearchSerializer()
        order_by_organization = OrganizationModelSerializer.Lite()
        short_return_items = ShortReturnItemModelSerializer.Details(many=True)

        class Meta(ShortReturnLogMeta):
            fields = ShortReturnLogMeta.fields + (
                'approved_by',
                'short_return_items',
                'status'
            )
            read_only_fields = ShortReturnLogMeta.read_only_fields + ()

    class Update(ListSerializer):
        class Meta(ShortReturnLogMeta):
            fields = ['status', ]
            read_only_fields = ShortReturnLogMeta.read_only_fields + ()


class ApproveShortReturnsSerializer(serializers.Serializer):
    """
    Serializer for For Approve Short Return
    """
    delivery_sheet = serializers.PrimaryKeyRelatedField(
        queryset=InvoiceGroupDeliverySheet().get_all_actives()
    )
    approved_by = serializers.PrimaryKeyRelatedField(
        queryset=PersonOrganization().get_all()
    )
