from elasticsearch_dsl import Q
from django.conf import settings
from rest_framework import generics

from common.enums import Status, PublishStatus
from core.custom_serializer.person_organization import PersonOrganizationModelSerializer

from search.utils import search_by_multiple_aliases

from core.enums import (
    PersonGroupType,
    PersonType,
    OrganizationType,
)

from core.serializers import (
    DepartmentSerializer,
    PersonOrganizationSupplierSerializer,
    PersonOrganizationCommonSerializer,
)
from core.custom_serializer.organization import (
    OrganizationModelSerializer
)

from core.custom_serializer.employee_designation import (
    EmployeeDesignationModelSerializer
)

from core.permissions import (
    CheckAnyPermission,
    StaffIsAccountant,
    StaffIsAdmin,
    StaffIsLaboratoryInCharge,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsSalesman,
    AnyLoggedInUser,
    IsSuperUser,
    StaffIsMonitor,
    StaffIsAdjustment,
    StaffIsTrader,
    StaffIsDeliveryMan,
    StaffIsMarketer,
    StaffIsTelemarketer,
    StaffIsDeliveryHub,
    StaffIsContactor,
    StaffIsSalesManager,
    StaffIsFrontDeskProductReturn,
    StaffIsProcurementManager,
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsSalesCoordinator,
    StaffIsProcurementCoordinator,
)


from ..document.users import (
    DepartmentDocument,
    EmployeeDesignationDocument,
    OrganizationDocument,
    PersonOrganizationDocument,
)


def is_digit_and_id(value):
    return value.isdigit() and len(value) < 10

class DepartmentSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = DepartmentDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias']
            )
        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=self.request.user.organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        response = search[:int(page_size)].execute()
        return response


class EmployeeSupplierPersonOrganizationSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = PersonOrganizationCommonSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PersonOrganizationDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['alias', 'first_name', 'last_name',
                        'company_name', 'phone', 'full_name']
            )
        search = search.query(
            Q('match', organization__pk=self.request.user.organization_id)
            & Q('match', status=Status.ACTIVE)
            & (Q('match', person_group=PersonGroupType.SUPPLIER)
            | Q('match', person_group=PersonGroupType.EMPLOYEE))
        )

        response = search[:int(page_size)].execute()
        return response


class EmployeeDesignationSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = EmployeeDesignationModelSerializer.Details

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = EmployeeDesignationDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias']
            )
        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=self.request.user.organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        response = search[:int(page_size)].execute()
        return response


class OrganizationSearchView(generics.ListAPIView):
    def get_permissions(self):
        if hasattr(self.request.user, 'organization_id'):
            is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        else:
            is_distributor = False
        if is_distributor:
            self.available_permission_classes = (
                IsSuperUser,
                StaffIsAccountant,
                StaffIsMonitor,
                StaffIsTrader,
                StaffIsAdmin,
                StaffIsReceptionist,
                StaffIsDeliveryMan,
                StaffIsMarketer,
                StaffIsTelemarketer,
                StaffIsDeliveryHub,
                StaffIsProcurementManager,
                StaffIsDistributionT1,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesCoordinator,
                StaffIsSalesManager,
            )
        else:
            self.available_permission_classes = (
                IsSuperUser,
                StaffIsAccountant,
                StaffIsMarketer,
                StaffIsMonitor,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsSalesManager,
                StaffIsProcurementManager,
                StaffIsDeliveryHub,
                StaffIsDistributionT1,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesCoordinator,
                StaffIsDeliveryHub
            )

        return (CheckAnyPermission(), )
    serializer_class = OrganizationModelSerializer.List
    def get_serializer_class(self):
        is_delivery_man = StaffIsDeliveryMan().has_permission(self.request, self.__class__)
        is_super_admin = IsSuperUser().has_permission(self.request, self.__class__)
        if is_delivery_man and not is_super_admin:
            return OrganizationModelSerializer.ListForDeliveryMan
        return OrganizationModelSerializer.List

    def get_query_status(self):
        """A method that return Status value for Organization
        Returns:
            [list] -- [A list, containing int]
        """
        status = [Status.ACTIVE, Status.SUSPEND, Status.DRAFT]
        status_query = self.request.query_params.get('status', None)
        if status_query and status_query.isdigit():
            status_code = int(status_query)
            if status_code in Status.get_sorted_values():
                status = [status_code, ]
        return status

    def get_queryset(self):
        is_trader = StaffIsTrader().has_permission(self.request, OrganizationSearchView)
        is_delivery_man = StaffIsDeliveryMan().has_permission(self.request, OrganizationSearchView)
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = OrganizationDocument.search()

        search, aliases = search_by_multiple_aliases(self.request, search)

        if query_value and query_value.isdigit():
            search = search.query(
                'bool',
                should=[
                    {'term': {'id': query_value}},
                    {'term': {'primary_mobile.raw': query_value}}
                ]
            )
        elif query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'primary_mobile', 'alias']
            )

        status = self.get_query_status()
        if is_trader:
            search = search.query(
                Q('match', entry_by__id=self.request.user.pk)
            )
        elif is_delivery_man:
            user_po_instance = self.request.user.get_person_organization_for_employee(
                only_fields=['id']
            )
            user_po_instance_id = user_po_instance.id if user_po_instance else 0

            search = search.query(
                Q('match', primary_responsible_person__id=user_po_instance_id) |
                Q('match', secondary_responsible_person__id=user_po_instance_id)
            )
        search = search.query(Q('terms', status=status)).sort('-id')
        response = search[:int(page_size)].execute()
        if aliases:
            self.pagination_class.page_size = search.count()

        return response


class PersonOrganizationSupplierSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        is_dropdown = self.request.query_params.get('drop_down', None)
        if is_dropdown:
            return PersonOrganizationCommonSerializer
        else:
            return PersonOrganizationSupplierSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PersonOrganizationDocument.search()

        search, aliases = search_by_multiple_aliases(self.request, search)

        user = self.request.user
        if not user.is_admin_or_super_admin():
            user_tagged_supplier_id = user.tagged_supplier_id
            if user_tagged_supplier_id:
                search = search.query(
                    Q('match', id=user_tagged_supplier_id)
                )

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['phone', 'email', 'company_name', 'alias']
            )
        search = search.query(
            Q('match', organization__pk=self.request.user.organization_id) &
            Q('match', status=Status.ACTIVE) &
            Q('match', person_group=PersonGroupType.SUPPLIER)
        )
        response = search[:int(page_size)].execute()
        if aliases:
            self.pagination_class.page_size = search.count()

        return response


class PersonOrganizationSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
        StaffIsDeliveryHub,
        StaffIsDistributionT1,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesManager,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = PersonOrganizationCommonSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PersonOrganizationDocument.search()

        search, aliases = search_by_multiple_aliases(self.request, search)

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'first_name', 'last_name', 'full_name', 'alias',
                    'phone', 'email', 'code', 'company_name'
                ]
            )
        query = Q("match", organization__pk=self.request.user.organization_id) \
            & Q('match', status=Status.ACTIVE)

        search = search.filter(query)
        # pharmacy type organization exclude referrer
        if self.request.user.profile_details.organization.type == OrganizationType.PHARMACY:
            search = search.filter(~Q('match', person_group=PersonGroupType.REFERRER))
        response = search[:int(page_size)].execute()
        if aliases:
            self.pagination_class.page_size = search.count()

        return response


class PersonOrganizationEmployeeSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsMarketer,
        StaffIsNurse,
        StaffIsPhysician,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsSalesManager,
        StaffIsAdjustment,
        StaffIsTrader,
        StaffIsTelemarketer,
        StaffIsDeliveryHub,
        StaffIsContactor,
        StaffIsFrontDeskProductReturn,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesCoordinator,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    def get_serializer_class(self):
        is_dropdown = self.request.query_params.get('drop_down', None)
        if is_dropdown:
            return PersonOrganizationCommonSerializer
        else:
            return PersonOrganizationModelSerializer.EmployeeSearch

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PersonOrganizationDocument.search()

        search, aliases = search_by_multiple_aliases(self.request, search)

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'first_name',
                    'last_name',
                    'full_name',
                    'phone',
                    'email',
                    'designation.name',
                    'designation.department.name',
                    'alias',
                    'code',
                ]
            )
        search = search.query(
            Q('terms', person_group=[PersonGroupType.EMPLOYEE, PersonGroupType.TRADER])
            & Q('match', organization__pk=self.request.user.organization_id)
            & Q('match', person_type=PersonType.INTERNAL)
            & Q('terms', status=[Status.ACTIVE, Status.DRAFT])
        ).sort('-id')
        response = search[:int(page_size)].execute()
        if aliases and search.count() > 20:
            self.pagination_class.page_size = search.count()

        return response


class PersonOrganizationContractorSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.query_params.get('drop_down', None):
            return PersonOrganizationCommonSerializer
        else:
            return PersonOrganizationModelSerializer.EmployeeSearch

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PersonOrganizationDocument.search()

        search, aliases = search_by_multiple_aliases(self.request, search)

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'first_name',
                    'last_name',
                    'full_name',
                    'phone',
                    'email',
                    'designation.name',
                    'designation.department.name',
                    'alias'
                ]
            )
        search = search.query(
            Q('terms', person_group=[PersonGroupType.CONTRACTOR])
            & Q('match', organization__pk=self.request.user.organization_id)
            & Q('match', person_type=PersonType.INTERNAL)
            & Q('terms', status=[Status.ACTIVE, Status.DRAFT])
        ).sort('-id')
        response = search[:int(page_size)].execute()
        if aliases and search.count() > 20:
            self.pagination_class.page_size = search.count()

        return response
