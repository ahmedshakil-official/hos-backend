from core.permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsDistributionT1,
    StaffIsProcurementOfficer,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from core.views.common_view import ListAPICustomView, RetrieveUpdateDestroyAPICustomView

from pharmacy.custom_serializer.product_changes_logs import ProductChangesLogsModelSerializer
from pharmacy.models import ProductChangesLogs
from pharmacy.filters import ProductChangesLogsFilter


class ProductChangesLogsList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    filterset_class = ProductChangesLogsFilter

    def get_queryset(self):
        return ProductChangesLogs.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductChangesLogsModelSerializer.List
        return ProductChangesLogsModelSerializer.List


class ProductChangesLogsDetail(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'product__alias'
    filterset_class = ProductChangesLogsFilter

    def get_queryset(self):
        alias = self.kwargs.get('product__alias')
        queryset = ProductChangesLogs.objects.filter(
            product__alias=alias
        )
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductChangesLogsModelSerializer.List
        return ProductChangesLogsModelSerializer.List
