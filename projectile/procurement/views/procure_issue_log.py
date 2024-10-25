from django.db import transaction

from common.pagination import CachedCountPageNumberPagination
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
    StaffIsProcurementOfficer,
    StaffIsProcurementManager,
    StaffIsDistributionT1,
    StaffIsProcurementCoordinator,
)
from procurement.serializers.procure_issue_log import ProcureIssueLogModelSerializer
from ..filters import ProcurementIssueReportFilter


class ProcureIssueListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = ProcurementIssueReportFilter
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcureIssueLogModelSerializer.List
        return ProcureIssueLogModelSerializer.Post

    def get_serializer(self, *args, **kwargs):
        """ if an array is passed, set serializer to many """
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self, related_fields=None, only_fields=None):
        return super().get_queryset(related_fields=related_fields, only_fields=only_fields).select_related(
            'supplier',
            'employee',
            'prediction_item',
        )
