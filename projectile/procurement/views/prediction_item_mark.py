from rest_framework.generics import (
    RetrieveUpdateAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework import status

from common.enums import Status, ActionType
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
    StaffIsProcurementCoordinator,
    StaffIsDistributionT1,
)
from procurement.serializers.prediction_item_mark import PredictionItemMarkModelSerializer
from ..models import Procure


class PredictionItemMarkListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PredictionItemMarkModelSerializer.List
        return PredictionItemMarkModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        return super().get_queryset(related_fields=related_fields, only_fields=only_fields).select_related(
            'supplier',
            'employee',
        )