
from rest_framework import generics, status
from rest_framework.response import Response
from ..permissions import (
    StaffIsAdmin,
)

from .common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)

from ..serializers import (

    DepartmentSerializer,
)
from common.enums import Status, PublishStatus

from ..models import (
    Department,
    EmployeeDesignation,
)
from django.db.models import Q
from django.db import transaction
from django.db.utils import IntegrityError
from core.custom_serializer.employee_designation import (
    EmployeeDesignationModelSerializer
)

from .search import OrganizationAndGlobalWiseSearch


class DepartmentList(ListCreateAPICustomView):
    serializer_class = DepartmentSerializer
    permission_classes = (StaffIsAdmin, )


class DepartmentSearch(OrganizationAndGlobalWiseSearch):
    serializer_class = DepartmentSerializer
    permission_classes = (StaffIsAdmin, )
    model_name = Department

    def get_queryset(self):
        return self.serve_queryset(self)


class DepartmentDetails(RetrieveUpdateDestroyAPICustomView):
    serializer_class = DepartmentSerializer
    permission_classes = (StaffIsAdmin, )
    lookup_field = 'alias'
    queryset = Department.objects.filter(status=Status.ACTIVE)


class EmployeeDesignationList(ListCreateAPICustomView):
    permission_classes = (StaffIsAdmin, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeDesignationModelSerializer.Details
        return EmployeeDesignationModelSerializer.List

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(
                    entry_by=self.request.user,
                    organization_id=self.request.user.organization_id
                )
                # get department name from department id
                department = Department.objects.get(
                    id=serializer.data['department'])

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDesignationSearch(OrganizationAndGlobalWiseSearch):
    serializer_class = EmployeeDesignationModelSerializer.Details
    permission_classes = (StaffIsAdmin, )

    model_name = EmployeeDesignation

    def get_queryset(self):
        return self.serve_queryset(self)


class EmployeeDesignationDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = EmployeeDesignation.objects.filter(status=Status.ACTIVE)
    permission_classes = (StaffIsAdmin, )
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeDesignationModelSerializer.Details
        return EmployeeDesignationModelSerializer.List


class EmployeeDesignationByDepartment(generics.ListAPIView):
    serializer_class = EmployeeDesignationModelSerializer.Details
    permission_classes = (StaffIsAdmin, )

    def get_queryset(self):
        alias = self.kwargs['alias']
        return EmployeeDesignation.objects.filter(
            ~Q(is_global=PublishStatus.PRIVATE) |
            Q(organization=self.request.user.organization_id)
        ).filter(department__alias=alias, status=Status.ACTIVE).order_by('pk')
