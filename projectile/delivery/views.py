from rest_framework.generics import (
    RetrieveUpdateAPIView,
    UpdateAPIView,
)
from common.enums import Status
from core.views.common_view import(
    ListCreateAPICustomView,
    CreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)
from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsDeliveryMan,
)

from .models import Delivery, StockDelivery
from .serializers.delivery import DeliveryModelSerializer
from .serializers.stock_delivery import StockDeliveryModelSerializer


class DeliveryList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDeliveryMan,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = DeliveryModelSerializer.List

    def get_queryset(self):
        user_po_instance = self.request.user.get_person_organization_for_employee(
            only_fields=['id']
        )
        is_superuser = IsSuperUser().has_permission(self.request, DeliveryList)
        queryset = super().get_queryset().select_related(
            'assigned_to',
            'assigned_by',
            'order_by_organization',
        ).prefetch_related(
            'orders',
        )
        if is_superuser:
            return queryset
        return queryset.filter(assigned_to=user_po_instance)


class DeliveryDetails(RetrieveUpdateAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDeliveryMan,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DeliveryModelSerializer.Details
        return DeliveryModelSerializer.StatusUpdate

    lookup_field = "alias"

    def get_queryset(self):
        user_po_instance = self.request.user.get_person_organization_for_employee(
            only_fields=['id']
        )
        is_superuser = IsSuperUser().has_permission(self.request, DeliveryDetails)
        queryset = Delivery.objects.select_related(
            'assigned_to',
            'assigned_by',
            'order_by_organization',
        ).prefetch_related(
            'orders',
        ).filter(
            status=Status.ACTIVE,
            organization_id=self.request.user.organization_id
        )
        if is_superuser:
            return queryset
        return queryset.filter(assigned_to=user_po_instance)

class UpdateStockDelivery(UpdateAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDeliveryMan,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = StockDeliveryModelSerializer.StatusUpdate

    lookup_field = "alias"
    lookup_url_kwarg = "product_alias"

    def get_queryset(self):
        delivery_alias = self.kwargs.get('delivery_alias')
        user_po_instance = self.request.user.get_person_organization_for_employee(
            only_fields=['id']
        )
        is_superuser = IsSuperUser().has_permission(self.request, DeliveryDetails)
        queryset = StockDelivery.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization_id=self.request.user.organization_id,
            delivery__alias=delivery_alias
        )
        if is_superuser:
            return queryset
        return queryset.filter(delivery__assigned_to=user_po_instance)
