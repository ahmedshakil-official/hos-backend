from django.core.cache import cache

from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response

from common.healthos_helpers import HealthOSHelper

from common.cache_keys import PRODUCT_STOCK_REMINDER_ORGANIZATION_KEY_PREFIX
from common.enums import Status
from common.pagination import  CachedCountPageNumberPagination
from core.permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsProcurementOfficer,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from core.views.common_view import ListCreateAPICustomView, ListAPICustomView
from pharmacy.custom_serializer.product_reminder import ProductRestockReminderModelSerializer
from pharmacy.models import StockReminder


healthos_helper = HealthOSHelper()


class ProductRestockReminderListCreate(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self):
        organization_aliases = self.request.query_params.get('organization_aliases', None)

        queryset = StockReminder.objects.filter(
            status=Status.ACTIVE,
        ).order_by('-id')

        if self.request.user.is_admin_or_super_admin() or self.request.user.organization_id == healthos_helper.organization_id():

            if organization_aliases:
                organization_aliases_list = [alias.strip() for alias in organization_aliases.split(',') if alias.strip()]

                queryset = queryset.filter(
                    organization__alias__in=organization_aliases_list
                )

            return queryset

        return queryset.filter(
            entry_by_id=self.request.user.id,
            organization__id=self.request.user.organization_id,
            status=Status.ACTIVE,
            reminder_count=0,
        ).order_by('-id')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            if self.request.user.is_admin_or_super_admin():
                return ProductRestockReminderModelSerializer.ListForAdmin
            return ProductRestockReminderModelSerializer.List
        else:
            return ProductRestockReminderModelSerializer.Post


class OrganizationWiseProductRestockReminderList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission,)
    pagination_class = None
    serializer_class = ProductRestockReminderModelSerializer.Lite

    def get_queryset(self):
        return StockReminder.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
            reminder_count=0,
        ).select_related(
            "stock"
        ).only(
            "stock__alias",
            "preferable_price",
        ).order_by("-id")

    def get(self, request, *args, **kwargs):
        organization_id = self.request.user.organization_id
        cache_key = PRODUCT_STOCK_REMINDER_ORGANIZATION_KEY_PREFIX + str(organization_id)
        # Attempt to retrieve serialized data from the cache
        cached_serialized_data = cache.get(cache_key)
        if cached_serialized_data is not None:
            return Response(cached_serialized_data, status=status.HTTP_200_OK)

        # If serialized data is not in the cache, retrieve from database
        queryset = self.get_queryset()
        serialized_data = self.serializer_class(queryset, many=True).data
        # Store the serialized data in the cache
        cache.set(cache_key, serialized_data)

        return Response(serialized_data, status=status.HTTP_200_OK)


class ProductRestockReminderUpdate(UpdateAPIView):
    available_permission_classes = (
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission,)

    lookup_field = 'alias'
    queryset = StockReminder.objects.filter(status=Status.ACTIVE, reminder_count=0)
    serializer_class = ProductRestockReminderModelSerializer.Update
