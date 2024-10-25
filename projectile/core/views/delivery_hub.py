from django.db.models import Q

from common.utils import validate_uuid4

from core.views.common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    StaffIsAccountant,
    StaffIsProcurementOfficer,
    StaffIsDeliveryHub,
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsAdmin,
    StaffIsProcurementManager,
    StaffIsSalesManager,
    StaffIsSalesCoordinator,
    StaffIsFrontDeskProductReturn,
    StaffIsTelemarketer,
    StaffIsDeliveryHub,
    StaffIsProcurementCoordinator,
)

from core.models import DeliveryHub

from core.custom_serializer.delivery_hub import DeliveryHubModelSerializer


class DeliveryHubList(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsAccountant,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsSalesManager,
        StaffIsSalesCoordinator,
        StaffIsDeliveryHub,
        StaffIsDistributionT1,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsTelemarketer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DeliveryHubModelSerializer.List

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = DeliveryHub().get_all_actives()
        keyword = self.request.query_params.get("keyword", None)

        # If a valid UUIDv4 is provided as the keyword, filter the queryset by 'alias'
        if keyword and validate_uuid4(keyword):
            queryset = queryset.filter(
                alias=keyword,
            )
        # filter the queryset by 'name' or 'short_code'
        elif keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) |
                Q(short_code__icontains=keyword)
            )

        return queryset


class DeliveryHubDetail(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    queryset = DeliveryHub().get_all_actives()
    lookup_field = "alias"
    serializer_class = DeliveryHubModelSerializer.Detail
