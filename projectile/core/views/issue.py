from django.db.models import Prefetch

from common.pagination import CachedCountPageNumberPagination
from core.views.common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
    ListAPICustomView
)
from core.permissions import (
    StaffIsReceptionist,
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    StaffIsSalesman,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsProcurementOfficer,
    StaffIsTrader,
    StaffIsTelemarketer,
    StaffIsDistributionT2,
    StaffIsFrontDeskProductReturn,
    StaffIsSalesManager,
    StaffIsDistributionT3,
    StaffIsDeliveryHub,
)
from core.custom_serializer.issue import IssueModelSerializer
from core.custom_serializer.issue_status import IssueStatusModelSerializer
from ..models import Issue, IssueStatus
from ..filters import IssueListFilter
from ..enums import OrganizationType


class IssueList(ListCreateAPICustomView):

    filterset_class = IssueListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsSalesman,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
                StaffIsDeliveryHub,
            )
        return (CheckAnyPermission(),)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return IssueModelSerializer.List
        else:
            return IssueModelSerializer.Post

    def get_queryset(self):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        is_trader = StaffIsTrader().has_permission(self.request, IssueList)
        queryset = Issue().get_all_actives().filter(
            organization__id=self.request.user.organization_id,
        ).select_related(
            'reported_to',
            'reported_against',
            'responsible_to_resolve',
            'issue_organization',
            'entry_by',
            'issue_organization__entry_by',
        )
        if is_trader:
            queryset = queryset.filter(
                entry_by__id=self.request.user.id
            )
        return queryset.order_by('-id')


class IssueDetails(RetrieveUpdateDestroyAPICustomView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return IssueModelSerializer.Details
        else:
            return IssueModelSerializer.Post

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsSalesman,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager
            )
        return (CheckAnyPermission(),)

    lookup_field = 'alias'

    def get_queryset(self):
        issue_status_queryset = IssueStatus().get_all_actives().order_by('-id')
        queryset = Issue().get_all_actives().prefetch_related(
            Prefetch('issue_status', queryset=issue_status_queryset)
        ).filter(
            organization__id=self.request.user.organization_id,
        ).select_related(
            'reported_to',
            'reported_against',
            'responsible_to_resolve',
            'issue_organization',
            'entry_by',
            'issue_organization__entry_by',
        )
        return queryset


class IssueStatusList(ListCreateAPICustomView):

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
            )
        return (CheckAnyPermission(),)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return IssueStatusModelSerializer.List
        else:
            return IssueStatusModelSerializer.Post
