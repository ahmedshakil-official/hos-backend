import contextlib
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
from ..permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsSalesman,
    StaffIsMarketer,
    StaffIsDeliveryHub,
    StaffIsProcurementManager,
    StaffIsDistributionT1,
    StaffIsDistributionT3,
    StaffIsSalesManager,
    StaffIsProcurementCoordinator,
)
from .common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
    ListAPICustomView,
)
from common.pagination import CachedCountPageNumberPagination

from ..serializers import (
    PersonOrganizationSupplierSerializer,
    PersonOrganizationSerializer,
    PersonOrganizationBasicSerializer,
    PersonOrganizationBasicGetOrCreateSerializer,
    PersonOrganizationEmployeeBasicSerializer,
    PersonOrganizationDetailsSerializer,
    PersonOrganizationSupplierGetSerializer,
)
from common.enums import Status

from ..models import (
    Person,
    Organization,
    PersonOrganizationGroupPermission,
    GroupPermission,
    PersonOrganization,
)
from django.db.models import Q
from ..enums import PersonGroupType, PersonType
from django.db import transaction
from django.db.utils import IntegrityError

from ..filters import (
    PersonOrganizationEmployeeListFilter
)
from common import helpers
from common.utils import (
    create_cache_key_name,
    sync_queryset,
)
from core.custom_serializer.person_organization import (
    PersonOrganizationModelSerializer,
    TraderBasicSerializer,
    ContractorSerializer,
)
from core.utils import update_permissions_for_person
from ..custom_serializer.person_organization_group_permission import (
    PersonOrganizationGroupPermissionModelSerializer
)

from ..custom_serializer.person_organization import PersonOrganizationEmployeeDetailsSerializer


class PersonOrganizationSupplierDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PersonOrganizationSupplierSerializer
    lookup_field = 'alias'
    deleted_cache_model_list = ['person', 'person_organization']

    queryset = PersonOrganization.objects.filter(
        person_group=PersonGroupType.SUPPLIER, status=Status.ACTIVE)

    @transaction.atomic
    def put(self, request, alias):
        person_organization = PersonOrganization.objects.get(alias=alias)
        try:
            serializer = PersonOrganizationSupplierSerializer(
                person_organization, data=request.data, context={
                    'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(
                    updated_by=self.request.user,
                )
                serializer_ = PersonOrganizationSupplierGetSerializer(
                    person_organization)
                return Response(
                    serializer_.data,
                    status=status.HTTP_200_OK
                )

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PersonOrganizationSupplierList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PersonOrganizationSupplierSerializer
    deleted_cache_model_list = ['person', 'person_organization']

    def get_queryset(self):
        key_name = create_cache_key_name(self, 'person_organization', 'list')
        cached_data_list = cache.get(key_name)
        if cached_data_list and False:
            data = cached_data_list
        else:
            data = PersonOrganization.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.ACTIVE,
                person_group=PersonGroupType.SUPPLIER
            ).order_by('pk')
            # cache.set(key_name, data)
        return data

    @transaction.atomic
    def create(self, request):
        try:
            serializer = PersonOrganizationSupplierSerializer(
                data=request.data, context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(
                    entry_by=self.request.user,
                    organization_id=self.request.user.organization_id
                )
                person_organization = PersonOrganization.objects.get(
                    organization=request.user.organization,
                    person_group=PersonGroupType.SUPPLIER,
                    person=serializer.data['id']
                )
                serializer_ = PersonOrganizationSupplierGetSerializer(
                    person_organization)
                return Response(
                    serializer_.data,
                    status=status.HTTP_201_CREATED
                )

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PersonOrganizationPermissionList(generics.ListCreateAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementCoordinator,
    )

    permission_classes = (
        CheckAnyPermission,
    )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PersonOrganizationGroupPermissionModelSerializer.List
        else:
            return PersonOrganizationGroupPermissionModelSerializer.Basic

    def get_queryset(self):
        return PersonOrganizationGroupPermission.objects.filter(
            person_organization__organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).select_related(
            'person_organization',
            'person_organization__person',
            'person_organization__organization',
            'permission'
        ).order_by('pk')

    def post(self, request, *args, **kwargs):
        # first start parsing the values
        try:
            person_organization = request.data.get('person_organization', None)
            items = request.data['permission_list']
            # Update prescriber prescription
            is_prescriber_permission = request.data.get(
                'is_prescriber_permission', None)
            if is_prescriber_permission:
                try:
                    # Find the id of Prescriber Group Permission
                    items[0]['permission'] = GroupPermission.objects.get(
                        name='Prescriber'
                    ).id
                except Exception as exception:
                    content = {'error': '{}'.format(exception)}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        # delete all the previous data
        person_organization_permissions = PersonOrganizationGroupPermission.objects.filter(
            person_organization__id=person_organization
        ).only('id')

        if person_organization_permissions.exists():
            # Delete permission cache
            person_organization_permissions.first(
            ).person_organization.person.delete_permission_cache()
            # Delete database rows
            person_organization_permissions._raw_delete(
                person_organization_permissions.db)

        try:
            serializer = PersonOrganizationGroupPermissionModelSerializer.Basic(
                data=items, many=True, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                serializer.save(entry_by=self.request.user)
                # Get the created permissions list to add it in person and person organization
                permission_ids = []
                for permission in serializer.data:
                    permission_ids.append(permission["permission"])
                # Update permissions for the person
                update_permissions_for_person(person_organization, permission_ids)

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PersonOrganizationPermissionDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (StaffIsAdmin, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PersonOrganizationGroupPermissionModelSerializer.List
        else:
            return PersonOrganizationGroupPermissionModelSerializer.Basic
    lookup_field = 'alias'

    def get_queryset(self):
        return PersonOrganizationGroupPermission.objects.filter(
            person_organization__organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).order_by('pk')


class OrganizationPersonGetOrCreate(generics.CreateAPIView):
    """This class will create person organization instance
    or return the existing instance
    """
    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsNurse,
        StaffIsPhysician,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PersonOrganizationBasicGetOrCreateSerializer

    def perform_create(self, serializer, extra_fields=None):
        # check if the data is valid
        if serializer.is_valid():
            organization_object = Organization.objects.get(
                pk=serializer.data['organization'])
            person_object = Person.objects.get(pk=serializer.data['person'])

            # now get or create
            try:
                person_organization_object = PersonOrganization.objects.get(
                    organization=organization_object,
                    person=person_object,
                    person_group=PersonGroupType.PATIENT,
                    status=Status.ACTIVE
                )
            except PersonOrganization.DoesNotExist:
                person_organization_object = PersonOrganization(
                    organization=organization_object,
                    person=person_object,
                    person_group=PersonGroupType.PATIENT,
                    status=Status.ACTIVE
                )

            # update the other data
            update_fields = [
                'email', 'phone', 'code', 'first_name', 'last_name', 'country', 'language',
                'permanent_address', 'present_address', 'dob', 'gender',
                'relatives_name', 'relatives_address', 'relatives_contact_number', 'relatives_relation',
                'family_relation', 'patient_refered_by', 'designation', 'joining_date', 'registration_number',
                'degree', 'remarks', 'medical_remarks', 'company_name',
            ]

            for field in update_fields:
                setattr(person_organization_object, field,
                        getattr(person_object, field))

            person_organization_object.save()

            # return the data as result
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # else show the error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PersonOrganizationEmployeeList(ListAPICustomView):
    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsNurse,
        StaffIsPhysician,
        StaffIsProcurementCoordinator,
        StaffIsSalesman,
        StaffIsMarketer,
        StaffIsDeliveryHub,
        StaffIsDistributionT1,
        StaffIsDistributionT3,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsSalesManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PersonOrganizationModelSerializer.EmployeeList
    filterset_class = PersonOrganizationEmployeeListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self):
        return sync_queryset(self, PersonOrganization.objects.select_related(
            'person',
            'designation',
            'designation__department',
        ).filter(
            status__in=[Status.ACTIVE, Status.DRAFT],
            organization=self.request.user.organization_id,
            person_group=PersonGroupType.EMPLOYEE,
            person_type=PersonType.INTERNAL
        ).order_by('-id'))


class PersonOrganizationEmployeeDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsDistributionT3,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsSalesManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    lookup_field = 'alias'

    def get_queryset(self):
        return PersonOrganization.objects.filter(
            person_group__in=[
                PersonGroupType.EMPLOYEE, PersonGroupType.SYSTEM_ADMIN],
            status__in=[Status.ACTIVE, Status.DRAFT])

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PersonOrganizationEmployeeDetailsSerializer
        return PersonOrganizationEmployeeBasicSerializer

    def perform_update(self, serializer):
        password = serializer.validated_data.get('password', None)
        delivery_hub = serializer.validated_data.get("delivery_hub", None)
        employee = Person.objects.get(
            person_organization__alias=self.kwargs.get('alias'))
        is_active = self.request.data.get('is_active', None)
        if is_active != None:
            is_active = helpers.to_boolean(is_active)
            employee.is_active = is_active

        if not password:
            del password
        else:
            employee.password = password
            del serializer.validated_data['confirm_password']
        email = serializer.validated_data.get('email', None)
        if email:
            employee.email = email
        phone = serializer.validated_data.get('phone', None)
        if phone:
            employee.phone = phone
        code = serializer.validated_data.get('code', None)
        if code:
            employee.code = code
        first_name = serializer.validated_data.get('first_name', None)
        if first_name:
            employee.first_name = first_name
        last_name = serializer.validated_data.get('last_name', None)
        if last_name:
            employee.last_name = last_name
        employee.updated_by_id = self.request.user.id
        if "delivery_hub" in self.request.data:
            employee.delivery_hub_id = delivery_hub
        employee.save(
            update_fields=[
                'is_active',
                'password',
                'email',
                'phone',
                'code',
                'first_name',
                'last_name',
                'updated_by_id',
                'delivery_hub',
            ]
        )
        serializer.save(updated_by_id=self.request.user.id)


class TraderList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = TraderBasicSerializer

    def get_queryset(self):
        return PersonOrganization.objects.filter(
            person_group=PersonGroupType.TRADER,
            organization=self.request.user.organization_id,
            status__in=[Status.ACTIVE, Status.DRAFT]
        ).order_by('pk')


class TraderDetails(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (StaffIsAdmin,)
    lookup_field = 'alias'

    def get_queryset(self):
        return PersonOrganization.objects.filter(
            person_group=PersonGroupType.TRADER,
            organization=self.request.user.organization_id,
            status__in=[Status.ACTIVE, Status.DRAFT])

    serializer_class = TraderBasicSerializer

    def perform_update(self, serializer):
        exclude_person_groups = [
            PersonGroupType.REFERRER,
            PersonGroupType.PATIENT,
            PersonGroupType.PRESCRIBER
        ]
        password = serializer.validated_data.get('password', None)
        try:
            employee = Person.objects.get(
                ~Q(person_group__in=exclude_person_groups),
                person_organization__alias=self.kwargs.get('alias'),
            )
            if not password:
                del password
            else:
                employee.password = password
                del serializer.validated_data['confirm_password']
            email = serializer.validated_data.get('email', None)
            if email:
                employee.email = email
            phone = serializer.validated_data.get('phone', None)
            if phone:
                employee.phone = phone
            employee.save(update_fields=['password', 'email', 'phone', ])
            serializer.save(updated_by=self.request.user)
        except (Person.MultipleObjectsReturned, Person.DoesNotExist):
            pass


class ContractorList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContractorSerializer.List
        return ContractorSerializer.Post

    def get_queryset(self):
        return PersonOrganization.objects.filter(
            person_group=PersonGroupType.CONTRACTOR,
            organization=self.request.user.organization_id,
            status__in=[Status.ACTIVE, Status.DRAFT]
        ).order_by('-pk')


class ContractorDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'alias'

    def get_queryset(self):
        return PersonOrganization.objects.filter(
            person_group=PersonGroupType.CONTRACTOR,
            organization=self.request.user.organization_id,
            status__in=[Status.ACTIVE, Status.DRAFT]
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContractorSerializer.List
        return ContractorSerializer.Update

    def perform_update(self, serializer):
        exclude_person_groups = [
            PersonGroupType.REFERRER,
            PersonGroupType.PATIENT,
            PersonGroupType.PRESCRIBER
        ]

        with contextlib.suppress(Person.MultipleObjectsReturned, Person.DoesNotExist):
            employee = Person.objects.get(
                ~Q(person_group__in=exclude_person_groups),
                person_organization__alias=self.kwargs.get('alias'),
                status__in=[Status.ACTIVE, Status.DRAFT]
            )

            # set is_active status for removing logging access
            is_active = self.request.data.get('is_active', None)
            if is_active != None:
                is_active = helpers.to_boolean(is_active)
                employee.is_active = is_active

            if password := serializer.validated_data.get('password', None):
                employee.password = password
                del serializer.validated_data['confirm_password']
            else:
                del password

            if email := serializer.validated_data.get('email', None):
                employee.email = email
            phone = serializer.validated_data.get('phone', None)
            if phone and phone != employee.phone:
                if existing_phone := Person.objects.filter(
                    ~Q(person_group=PersonGroupType.EMPLOYEE) & Q(phone=phone)
                ).exists():
                    raise ValidationError({"phone": ["This field must be unique."]})
                else:
                    employee.phone = phone
            employee.save(update_fields=['email', 'phone', 'is_active', 'password'])
            serializer.save(updated_by=self.request.user)
