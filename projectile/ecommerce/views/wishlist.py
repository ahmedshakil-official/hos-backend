from rest_framework import status
from rest_framework.response import Response

from common.enums import Status
from common.healthos_helpers import HealthOSHelper
from core.permissions import (
    StaffIsAdmin, StaffIsSalesman,
    StaffIsNurse, StaffIsProcurementOfficer,
    CheckAnyPermission,
    StaffIsProcurementManager,
)
from core.views.common_view import ListCreateAPICustomView, RetrieveUpdateDestroyAPICustomView, ListAPICustomView
from ecommerce.models import Wishlist, WishlistItem
from ecommerce.serializers.wishlist import WishlistModelSerializer
from ecommerce.serializers.wishlist_item import WishlistItemModelSerializer

healthos_helper = HealthOSHelper()

class WishlistListDetails(RetrieveUpdateDestroyAPICustomView):
    lookup_field = 'alias'
    serializer_class = WishlistModelSerializer.List
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        alias = self.kwargs.get('alias')
        return Wishlist.objects.filter(
            status=Status.ACTIVE,
            alias=alias,
        )


class WishlistListCreate(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.organization_id == healthos_helper.organization_id():
            return Wishlist.objects.filter(
                status=Status.ACTIVE,
            ).order_by('-id')
        return Wishlist.objects.filter(
            organization__id=self.request.user.organization_id,
            status=Status.ACTIVE,
        ).order_by('-id')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WishlistModelSerializer.Lite
        else:
            return WishlistItemModelSerializer.Post


class OrganizationWishlistItems(ListAPICustomView):
    serializer_class = WishlistItemModelSerializer.List
    pagination_class = None

    def get_queryset(self):
        return WishlistItem.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
        )


class WishlistItemRetrieveDelete(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsNurse,
        StaffIsProcurementOfficer,
    )
    lookup_field = 'alias'
    serializer_class = WishlistItemModelSerializer.List
    queryset = WishlistItem.objects.filter(
        status=Status.ACTIVE,
    )


class WishlistItemsStockAliasList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    pagination_class = None

    def get_queryset(self):
        return WishlistItem.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        stock_aliases = queryset.values_list('stock__alias', flat=True)

        return Response(data=stock_aliases, status=status.HTTP_200_OK)
