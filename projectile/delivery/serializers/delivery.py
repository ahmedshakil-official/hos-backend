from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status

from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.custom_serializer.organization import OrganizationModelSerializer

from pharmacy.custom_serializer.purchase import (
    DeliveryOrderListSerializer,
    DeliveryOrderDetailsSerializer,
)

from ..models import Delivery
from ..enums import DeliveryTrackingStatus


class DeliveryMeta(ListSerializer.Meta):
    model = Delivery
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class DeliveryModelSerializer:

    class List(ListSerializer):
        assigned_by = PersonOrganizationEmployeeSearchSerializer()
        assigned_to = PersonOrganizationEmployeeSearchSerializer()
        order_by_organization = OrganizationModelSerializer.Lite(read_only=True)
        orders = DeliveryOrderListSerializer(many=True)

        class Meta(DeliveryMeta):
            fields = ListSerializer.Meta.fields + (
                'date',
                'amount',
                'discount',
                'grand_total',
                'round_discount',
                'tracking_status',
                'assigned_by',
                'assigned_to',
                'order_by_organization',
                'orders',
            )
            read_only_fields = DeliveryMeta.read_only_fields + ()

    class Details(List):
        assigned_by = PersonOrganizationEmployeeSearchSerializer()
        assigned_to = PersonOrganizationEmployeeSearchSerializer()
        order_by_organization = OrganizationModelSerializer.Lite(read_only=True)
        orders = DeliveryOrderDetailsSerializer(many=True)

        class Meta(DeliveryMeta):
            fields = ListSerializer.Meta.fields + (
                'date',
                'amount',
                'discount',
                'grand_total',
                'round_discount',
                'tracking_status',
                'assigned_by',
                'assigned_to',
                'order_by_organization',
                'orders',
            )
            read_only_fields = DeliveryMeta.read_only_fields + ()

    class StatusUpdate(ListSerializer):
        def validate_tracking_status(self, value):
            valid_values = [
                DeliveryTrackingStatus.ON_THE_WAY,
                DeliveryTrackingStatus.DELIVERED,
                DeliveryTrackingStatus.PARITAL_DELIVERED,
                DeliveryTrackingStatus.FULL_RETURNED,
            ]
            stock_delivery_qs = self.instance.stockdelivery_set.filter(
                status=Status.DISTRIBUTOR_ORDER,
            )
            if value in valid_values:
                if value == DeliveryTrackingStatus.DELIVERED:
                    stock_deliveries = stock_delivery_qs.filter(
                        tracking_status=DeliveryTrackingStatus.FULL_RETURNED
                    )
                    if stock_deliveries.exists():
                        serializers.ValidationError(
                            'DELIVERY_WITH_RETURNED_ITEM_SHOULD_BE_FULL_RETURNED_OR_PARTIAL_DELIVERED'
                        )
                return value
            else:
                raise serializers.ValidationError('INVALID_VALUE')

        class Meta(DeliveryMeta):
            fields = ListSerializer.Meta.fields + (
                'tracking_status',
            )
            read_only_fields = DeliveryMeta.read_only_fields + ()
