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
from core.views.common_view import ListAPICustomView, RetrieveUpdateDestroyAPICustomView
from ecommerce.serializers.invoice_group_pdf import InvoiceGroupPdfModelSerializer
from ecommerce.models import InvoiceGroupPdf
from ecommerce.filters import InvoiceGroupPdfListFilter


class InvoiceGroupPDFList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesManager,
        StaffIsSalesCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = InvoiceGroupPdfModelSerializer.List
    filterset_class = InvoiceGroupPdfListFilter
    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = InvoiceGroupPdf().get_all_actives()
        return queryset


class InvoiceGroupPdfDetails(RetrieveUpdateDestroyAPICustomView):
    lookup_field = "alias"
    serializer_class = InvoiceGroupPdfModelSerializer.List

    def get_queryset(self):
        return InvoiceGroupPdf.objects.filter()
