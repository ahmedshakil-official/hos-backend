from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsNurse,
    StaffIsProcurementOfficer,
    StaffIsSalesman,
    StaffIsReceptionist,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    IsSuperUser,
    StaffIsMonitor,
    StaffIsSalesReturn,
    StaffIsAdjustment,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsSalesCoordinator,
    StaffIsSalesManager,
)
from core.views.common_view import ListCreateAPICustomView, RetrieveUpdateDestroyAPICustomView
from ecommerce.serializers.invoice_pdf_group import InvoicePdfGroupModelSerializer
from ecommerce.models import InvoicePdfGroup
from ecommerce.filters import InvoicePdfGroupListFilter


class InvoicePdfGroupList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesManager,
        StaffIsSalesCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    filterset_class = InvoicePdfGroupListFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return InvoicePdfGroupModelSerializer.List
        return InvoicePdfGroupModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = InvoicePdfGroup().get_all_actives()
        return queryset


class InvoicePdfGroupDetails(RetrieveUpdateDestroyAPICustomView):
    lookup_field = "alias"
    serializer_class = InvoicePdfGroupModelSerializer.Details

    def get_queryset(self):
        return InvoicePdfGroup.objects.filter()
