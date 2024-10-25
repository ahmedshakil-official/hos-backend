import datetime

from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.enums import Status
from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsProcurementOfficer,
    StaffIsTelemarketer,
    StaffIsSalesCoordinator,
    StaffIsSalesManager,
    StaffIsDeliveryHub,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsFrontDeskProductReturn,
)
from core.views.common_view import ListCreateAPICustomView, ListAPICustomView
from ..custom_serializer.order_tracking import (
    OrderTrackingModelSerializer,
)
from ..filters import OrderStatusChangeLogFilter
from ..models import OrderTracking


class OrderTrackingList(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsSalesCoordinator,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager
    )
    serializer_class = OrderTrackingModelSerializer.List

    def get_queryset(self):
        queryset = OrderTracking().get_all_actives()
        return queryset

    def perform_create(self, serializer, extra_fields=None):
        updated_fields = ['updated_by']
        responsible_employee = self.request.data.get('responsible_employee', None)
        order = serializer.validated_data.get('order', None)
        order_status = serializer.validated_data.get('order_status', None)
        if order and order_status:
            order.current_order_status = order_status
            updated_fields.append('current_order_status')
        if order and responsible_employee and isinstance(responsible_employee, int):
            order.responsible_employee_id = responsible_employee
            updated_fields.append('responsible_employee')
        order.updated_by_id = self.request.user.id
        order.save(update_fields=updated_fields)
        super().perform_create(serializer)


class OrderTrackingStatusChangeLog(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesCoordinator,
        StaffIsSalesManager
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = OrderTrackingModelSerializer.StatusChangeLog
    filterset_class = OrderStatusChangeLogFilter

    def get_queryset(self):
        queryset = OrderTracking.objects.filter(
            order__invoice_group__isnull=False,
        ).exclude(
            status=Status.INACTIVE,
        ).select_related(
            'order',
        ).order_by('-created_at')
        return queryset


