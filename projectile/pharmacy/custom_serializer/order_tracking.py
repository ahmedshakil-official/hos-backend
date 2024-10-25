import os

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)
from common.enums import Status
from ecommerce.models import OrderInvoiceGroup
from ..enums import OrderTrackingStatus
from ..models import OrderTracking
from core.custom_serializer.person import PersonModelSerializer

# pylint: disable=old-style-class, no-init
class OrderTrackingMeta(ListSerializer.Meta):
    model = OrderTracking
    fields = ListSerializer.Meta.fields + (
        'order_status',
        'order',
        'failed_delivery_reason',
        'remarks',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class OrderTrackingModelSerializer:
    class List(ListSerializer):
        '''
        This serializer will be used to list/create OrderTracking model
        '''

        # def validate(self, data):
        #     order = data.get("order")
        #     order_status = data.get("order_status")
        #     request = self.context.get('request', None)
        #     is_superuser = request and request.user.is_superuser

        #     if not order.is_valid_tracking_status(order_status) and not is_superuser:
        #         raise serializers.ValidationError({
        #             'order_status': _("Order Status Can't be duplicate."),
        #         })
        #     return data

        # pylint: disable=old-style-class, no-init

        class Meta(OrderTrackingMeta):
            pass

        def validate(self, attrs):
            from core.enums import OrganizationType
            from datetime import date

            ignore_validate = self.context.get("ignore_validate", False)
            if ignore_validate:
                return attrs
            request = self.context.get("request")
            order = attrs.get("order")
            is_superuser = request.user.is_superuser
            today_date = date.today()
            tentative_delivery_date = order.tentative_delivery_date
            allowed_days = 7
            delta = today_date - tentative_delivery_date
            if not is_superuser and delta.days > allowed_days:
                message = f"Status change is not permitted, the order is older than {delta.days} days"
                raise serializers.ValidationError({
                    "error": message,
                })

            organization_id = request.user.organization_id
            is_distributor = request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
            order_status = attrs.get("order_status")
            if order_status in [OrderTrackingStatus.CANCELLED, OrderTrackingStatus.REJECTED]:
                if order.invoice_group_id:
                    order_invoice_group_id = order.invoice_group_id
                    if str(organization_id) == os.environ.get("DISTRIBUTOR_ORG_ID", "") or is_distributor:
                        message = f"""You can't change this order's status as it belongs to an Invoice Group #{order_invoice_group_id}.
                        Please change status from Invoice Group List.
                        """
                        raise serializers.ValidationError({
                            "error": message,
                        })
                    message = f"We are processing you order, You can't cancel it."
                    raise serializers.ValidationError({
                        "detail": message,
                    })
            return attrs

    class ListWithEntryBy(ListSerializer):
        entry_by = PersonModelSerializer.EntryBy(read_only=True)

        class Meta(OrderTrackingMeta):
            fields = OrderTrackingMeta.fields + (
                'date',
                'order',
                'entry_by',
            )

    class StatusChangeLog(ListSerializer):
        invoice_group = serializers.IntegerField()
        delivery_date = serializers.DateField()
        entry_by = PersonModelSerializer.EntryBy(read_only=True)

        class Meta(OrderTrackingMeta):
            fields = (
                'date',
                'order',
                'invoice_group',
                'delivery_date',
                'order_status',
                'created_at',
                'entry_by',
            )
