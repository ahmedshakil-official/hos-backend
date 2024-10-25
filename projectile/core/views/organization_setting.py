
from rest_framework import generics
import logging
from ..permissions import (
    StaffIsAdmin,
    StaffIsProcurementManager,
    AnyLoggedInUser,
    CheckAnyPermission,
)

from .common_view import (
    ListCreateAPICustomView,
)

from common.enums import Status
from common.pagination import CachedCountPageNumberPagination

from ..models import (
    OrganizationSetting,
)
from django.db.utils import IntegrityError

from core.custom_serializer.organization_setting import (
    OrganizationSettingModelSerializer
)

logger = logging.getLogger(__name__)


class OrganizationSettings(ListCreateAPICustomView):
    pagination_class = CachedCountPageNumberPagination

    permission_classes = (AnyLoggedInUser, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrganizationSettingModelSerializer.List
        else:
            return OrganizationSettingModelSerializer.Basic

    def get_queryset(self):
        return OrganizationSetting.objects.filter(
            status=Status.ACTIVE,
            organization_id=self.request.user.organization_id
        ).select_related(
            "organization",
            "organization__delivery_hub",
            "organization__entry_by",
            "organization__primary_responsible_person",
            "organization__secondary_responsible_person",
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        id_of_queryset = queryset.values_list('id', flat=True)
        return self.get_from_cache(
            queryset=id_of_queryset,
            request=request
        )


class OrganizationSettingDetails(generics.RetrieveUpdateDestroyAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    queryset = OrganizationSetting.objects.filter(status=Status.ACTIVE)
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrganizationSettingModelSerializer.List
        else:
            return OrganizationSettingModelSerializer.Basic
