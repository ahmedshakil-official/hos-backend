from rest_framework.response import Response
from rest_framework import status

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
    StaffIsDistributionT1,
    StaffIsProcurementOfficer,
    StaffIsContactor,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from procurement.serializers.procure_status import ProcureStatusModelSerializer
from procurement.models import ProcureStatus


class ProcureStatusListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsProcurementOfficer,
        StaffIsContactor,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcureStatusModelSerializer.List
        return ProcureStatusModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        return ProcureStatus().get_all_actives()
