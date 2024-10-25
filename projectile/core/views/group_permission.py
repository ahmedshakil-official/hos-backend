
from rest_framework import generics
from ..permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsAccountant,
    AnyLoggedInUser,
    StaffIsProcurementCoordinator,
)

from .common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)

from ..serializers import (
    PersonOrganizationSerializer,
)
from common.enums import Status
from common.pagination import TwoHundredResultsSetPagination

from ..models import (
    PersonOrganizationGroupPermission,
    GroupPermission,
    PersonOrganization,
)
from ..enums import PersonGroupType

from core.enums import OrganizationType

from ..custom_serializer.group_permission import (
    GroupPermissionModelSerializer
)


class OrganizationPermissionGroupList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = GroupPermissionModelSerializer.List
    pagination_class = TwoHundredResultsSetPagination

    def get_queryset(self):
        distributor_organization = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        queryset = GroupPermission.objects.filter(
            status=Status.ACTIVE
        ).order_by('pk')
        if not distributor_organization:
            return queryset.exclude(name="DeliveryMan")
        else:
            return queryset


class OrganizationPermissionGroupDetails(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (StaffIsAdmin, )
    serializer_class = GroupPermissionModelSerializer.List
    lookup_field = 'alias'

    def get_queryset(self):
        return GroupPermission.objects.filter(
            status=Status.ACTIVE
        ).order_by('pk')


class OrganizationEmployeePermissionGroupList(generics.ListAPIView):
    permission_classes = (AnyLoggedInUser, )
    """Permission Group List of an Employee"""
    serializer_class = GroupPermissionModelSerializer.List
    pagination_class = TwoHundredResultsSetPagination

    def get_queryset(self):
        employee_alias = self.request.query_params.get('employee_alias', None)
        # If no employee is pass as params then the employee will be request user
        if not employee_alias:
            employee_alias = self.request.user.alias
        query = PersonOrganizationGroupPermission.objects.filter(
            status=Status.ACTIVE,
            person_organization__organization__id=self.request.user.organization_id,
            person_organization__person__alias=employee_alias
        ).select_related(
            'permission',
        ).order_by('pk')
        permission_groups = list(set([item.permission for item in query]))
        serializer = GroupPermissionModelSerializer.List(
            permission_groups, many="true")
        return serializer.data


class OrganizationEmployeePermissionList(generics.ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PersonOrganizationSerializer

    def get_queryset(self):
        employee_alias = self.kwargs.get("alias", "")
        return PersonOrganization.objects.filter(
            organization=self.request.user.organization_id,
            person__alias=employee_alias,
            person_group=PersonGroupType.EMPLOYEE,
            status=Status.ACTIVE
        ).order_by('pk')
