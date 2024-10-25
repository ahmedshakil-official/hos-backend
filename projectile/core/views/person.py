from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView

from common.helpers import generate_phone_no_for_sending_sms
from ..choices import ResetStatus, ResetType
from ..permissions import (
    IsSuperUser,
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsProcurementOfficer,
    AnyLoggedInUser,
    StaffIsMonitor,
    StaffIsTrader,
    StaffIsDeliveryMan,
    StaffIsTelemarketer,
    StaffIsMarketer,
    StaffIsDeliveryHub,
    StaffIsSalesManager,
    StaffIsDistributionT3,
    StaffIsDistributionT1,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)

from .common_view import (
    ListAPICustomView,
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)
from common.pagination import CachedCountPageNumberPagination

from ..serializers import (
    EmployeeSerializer,
    EmployeeBasicSerializer,
    SupplierBasicSerializer,
    PersonOrganizationEmployeeBasicSerializer,
    UserPasswordResetListSerializer,
)
from common.enums import Status

from core.custom_serializer.person import PersonModelSerializer

from ..models import (
    Person,
    EmployeeDesignation,
    Organization,
    OrganizationSetting,
    PersonOrganizationGroupPermission,
    GroupPermission,
    PersonOrganization,
    PasswordReset,
)
from django.utils import timezone
from django.db.models import Q, F
from ..enums import PersonGroupType
from django.db import transaction
from django.db.utils import IntegrityError

from ..utils import (
    get_person_and_person_organization_common_arguments,
    create_person_organization,
    get_organization_order_insights,
)
from ..filters import (
    OrganizationListFilter, PasswordResetFilter
)
from core.custom_serializer.organization import (
    OrganizationModelSerializer
)
from common import helpers
import random
import string
import os
from django.contrib.auth.hashers import make_password
from common.tasks import (
    send_sms,
    send_same_sms_to_multiple_receivers,
    send_message_to_slack_or_mattermost_channel_lazy,
)
from common.utils import (
    parse_to_dict_vals,
    DistinctSum,
)
from core.custom_serializer.person_organization import (
    DistributorBuyerUserCreateSerializer,
)

from pharmacy.enums import StorePointType
from core.enums import OrganizationType
from pharmacy.models import StorePoint
from promotion.models import PopUpMessage, PublishedPopUpMessage

class EmployeeList(ListCreateAPICustomView):
    available_permission_classes = ()

    def get_permissions(self):
        if self.request.method == "GET":
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsDistributionT3,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsSalesManager,
                StaffIsProcurementCoordinator,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDeliveryHub,
                StaffIsDistributionT1,
                StaffIsDistributionT3,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsSalesManager,
                StaffIsProcurementCoordinator,
            )
        return (CheckAnyPermission(),)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeSerializer
        else:
            return EmployeeBasicSerializer

    def get_queryset(self):
        return Person.objects.filter(
            person_group=PersonGroupType.EMPLOYEE,
            organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).order_by('-id')

    @transaction.atomic
    def create(self, request, *arg, **kwarg):
        serializer = self.get_serializer(data=request.data)
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(
                        organization_id=self.request.user.organization_id,
                        entry_by=self.request.user
                    )

                    try:
                        person_organization_employee = PersonOrganization.objects.get(
                            organization=self.request.user.organization_id,
                            person_group=PersonGroupType.EMPLOYEE,
                            person_id=serializer.data['id'],
                            phone=serializer.data['phone'],
                        )
                    except (PersonOrganization.DoesNotExist, PersonOrganization.MultipleObjectsReturned):
                        pass

                    if person_organization_employee:
                        response_data = \
                            PersonOrganizationEmployeeBasicSerializer(
                                person_organization_employee
                            )
                    return Response(
                        response_data.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetails(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (StaffIsAdmin,)
    queryset = Person.objects.filter(
        person_group=PersonGroupType.EMPLOYEE, status=Status.ACTIVE)
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeSerializer
        else:
            return EmployeeBasicSerializer

    def perform_update(self, serializer):
        if self.request.method != 'PATCH':
            if not serializer.validated_data['password']:
                del serializer.validated_data['password']
            del serializer.validated_data['confirm_password']
        serializer.save(updated_by=self.request.user)


class OrganizationList(generics.ListCreateAPIView):

    available_permission_classes = ()

    '''
        organization List Filter add
    '''
    filterset_class = OrganizationListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                IsSuperUser,
                StaffIsMonitor,
                StaffIsTrader,
                StaffIsDeliveryMan,
                StaffIsMarketer,
                StaffIsDistributionT3,
                StaffIsSalesManager,
                StaffIsTelemarketer,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                IsSuperUser,
                StaffIsTrader,
                StaffIsTelemarketer,
                StaffIsDistributionT3,
                StaffIsSalesManager,
            )

        return (CheckAnyPermission(), )

    def get_queryset(self):
        is_trader = StaffIsTrader().has_permission(self.request, OrganizationList)
        is_delivery_man = StaffIsDeliveryMan().has_permission(
            self.request, OrganizationList)
        queryset = Organization.objects.select_related(
            'entry_by',
            'referrer',
            'primary_responsible_person',
            'secondary_responsible_person',
            "delivery_hub",
            'area',
        ).filter(
            status__in=[Status.ACTIVE, Status.SUSPEND, Status.DRAFT]
        ).order_by('-pk')
        if is_trader:
            return queryset.filter(entry_by__id=self.request.user.id)
        elif is_delivery_man:
            return queryset.filter(
                Q(primary_responsible_person__person__id=self.request.user.id) |
                Q(secondary_responsible_person__person__id=self.request.user.id)
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            is_delivery_man = StaffIsDeliveryMan().has_permission(
                self.request, OrganizationList)
            is_super_admin = IsSuperUser().has_permission(self.request, OrganizationList)
            if is_delivery_man and not is_super_admin:
                return OrganizationModelSerializer.ListForDeliveryMan
            return OrganizationModelSerializer.List
        else:
            return OrganizationModelSerializer.Post

    def send_sms_with_credential(self, user):
        url = "https://ecom.healthosbd.com"
        full_name = "{} {}".format(user.first_name, user.last_name)
        phone = helpers.generate_phone_no_for_sending_sms(user.phone)
        random_pass = "".join(random.choice(string.digits) for _ in range(6))
        user.password = make_password(random_pass)
        user.save(update_fields=['password'])
        sms_text = "Dear {},\nPlease goto {} and login with following credential.\nPhone: {},\nPassword: {}.".format(
            full_name, url, user.phone, random_pass
        )
        # Sending sms to client
        send_sms.delay(
            phone,
            sms_text,
            user.organization.id
        )
        # HealthOS Management
        phone_numbers = os.environ.get(
            'NUMBERS_FOR_RECEIVING_ORG_USER_ADD_CREDENTIAL_MESSAGE', '')
        if not phone_numbers:
            return
        phone_numbers = phone_numbers.split(',') if phone_numbers else []
        phone_numbers = ", ".join(
            list(map(lambda phone: "880{}".format(phone[-10:]), phone_numbers)))
        phone_numbers = [item.strip() for item in phone_numbers.split(',')]
        # Sending sms to HealthOS
        send_same_sms_to_multiple_receivers.delay(phone_numbers, sms_text)

    def send_sms_to_trader_and_healthos(self, user):
        trader = self.request.user
        trader_name = "{} {}".format(trader.first_name, trader.last_name)
        trader_phone = helpers.generate_phone_no_for_sending_sms(trader.phone)
        trader_sms_text = "Dear {},\nYou have added a new organization named {}.".format(
            trader_name,
            user.organization.name
        )
        # Sending sms to Trader
        send_sms.delay(
            trader_phone,
            trader_sms_text,
            trader.organization_id
        )
        # HealthOS Management
        phone_numbers = os.environ.get(
            'NUMBER_FOR_RECEIVING_ORG_ADD_MESSAGE', '')
        if not phone_numbers:
            return
        phone_numbers = phone_numbers.split(',') if phone_numbers else []
        phone_numbers = ", ".join(
            list(map(lambda phone: "880{}".format(phone[-10:]), phone_numbers)))
        phone_numbers = [item.strip() for item in phone_numbers.split(',')]
        healthos_sms_text = "New Distributor Buyer type organization added.\nName: {},\nAddress: {},\nAdded By: {}.".format(
            user.organization.name,
            user.organization.address,
            trader_name
        )
        # Sending sms to HealthOS
        send_same_sms_to_multiple_receivers.delay(
            phone_numbers, healthos_sms_text)
        # Send message to slack channel
        send_message_to_slack_or_mattermost_channel_lazy.delay(
            os.environ.get('HOS_PHARMA_CHANNEL_ID', ""),
            healthos_sms_text
        )

    def prepare_user_data(self, request):
        form_data = {k: v[0] if len(
            v) == 1 else v for k, v in request.POST.lists()}
        user_data = request.data.get(
            'user_data', parse_to_dict_vals(form_data))
        return user_data

    def create(self, request):
        try:
            with transaction.atomic():
                serial_type = request.data.get('serial_type', None)
                store_point = request.data.get('store_point', None)
                show_global_product = request.data.get(
                    'show_global_product', False)
                global_product_category = request.data.get(
                    'global_product_category', None)
                global_subservice_category = request.data.get(
                    'global_subservice_category', None)
                package = request.data.get('package', None)
                referrer_id = request.data.get('referrer', None)
                user_data = self.prepare_user_data(request)
                _user = None
                serializer = self.get_serializer(
                    data=request.data,
                    context={'request': request}
                )
                if serializer.is_valid(raise_exception=True):
                    _data = {
                        'entry_by_id': self.request.user.id
                    }
                    if referrer_id:
                        _data['referrer_id'] = referrer_id
                    organization_instance = serializer.save(**_data)
                    # Create a user with credential and Admin permission
                    if user_data and user_data is not None:
                        try:
                            user = DistributorBuyerUserCreateSerializer(
                                data=user_data, context={'request': request})
                            if user.is_valid(raise_exception=True):
                                _user = user.save(
                                    entry_by=self.request.user,
                                    organization_id=serializer.data['id']
                                )
                                person_organization = _user.get_person_organization_for_employee()
                                permission = GroupPermission().get_instance_by_property(
                                    {'name': 'Admin'}
                                )
                                # Create Admin permission for the user
                                if person_organization and permission:
                                    PersonOrganizationGroupPermission.objects.get_or_create(
                                        person_organization=person_organization,
                                        permission=permission
                                    )
                        except Exception as exception:
                            _user = None
                            content = {'error': '{}'.format(exception)}
                            return Response(content, status=status.HTTP_400_BAD_REQUEST)
                    setting = OrganizationSetting.objects.get(
                        organization=serializer.data['id'],
                        status=Status.ACTIVE
                    )
                    if serial_type:
                        setting.serial_type = serial_type
                    if global_product_category:
                        setting.global_product_category = global_product_category
                    if global_subservice_category:
                        setting.global_subservice_category = global_subservice_category
                    if package:
                        setting.package = package
                    setting.save()
                    store_point_type = StorePointType.PHARMACY

                    # Create vendor default type store point for distributor type organization
                    if serializer.data['type'] == OrganizationType.DISTRIBUTOR:
                        store_point_type = StorePointType.VENDOR
                        vendor_default_store_point = "{}..".format(
                            serializer.data['name'])
                        vendor_default_store_point = StorePoint.objects.create(
                            name=vendor_default_store_point,
                            phone=serializer.data['primary_mobile'],
                            address=serializer.data['address'],
                            organization_id=serializer.data['id'],
                            type=StorePointType.VENDOR_DEFAULT
                        )
                        vendor_default_store_point.save()
                    if store_point:
                        store_point = StorePoint.objects.create(
                            name=serializer.data['name'],
                            phone=serializer.data['primary_mobile'],
                            address=serializer.data['address'],
                            organization_id=serializer.data['id'],
                            populate_global_product=show_global_product,
                            type=store_point_type
                        )
                        store_point.save()
                        setting.default_storepoint = store_point
                        setting.save(update_fields=['default_storepoint'])

                    # Send SMS
                    if _user is not None:
                        self.send_sms_with_credential(_user)
                        self.send_sms_to_trader_and_healthos(_user)
                    return Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED
                    )

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetails(generics.RetrieveUpdateDestroyAPIView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDistributionT3,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    queryset = Organization.objects.filter(
        status__in=[Status.ACTIVE, Status.SUSPEND, Status.DRAFT]
    ).select_related(
        "area",
        "delivery_hub",
        "referrer",
        "primary_responsible_person",
        "secondary_responsible_person",
        "entry_by"
    )
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrganizationModelSerializer.Details
        else:
            return OrganizationModelSerializer.Post

    def approve_registration(self, user_id):
        _user = Person.objects.only(
            'id',
            'first_name',
            'last_name',
            'phone',
        ).get(pk=user_id)
        person_organization = _user.get_person_organization_for_employee(
            only_fields=['id']
        )
        permission = GroupPermission().get_instance_by_property(
            {'name': 'Admin'}
        )
        # Create Admin permission for the user
        if person_organization and permission:
            PersonOrganizationGroupPermission.objects.get_or_create(
                person_organization_id=person_organization.id,
                permission=permission
            )
        # Add user as buyer
        # buyer_phone = _user.phone if _user else None
        # _user.organization.add_as_distributor_buyer(buyer_phone)

        full_name = f"{_user.first_name} {_user.last_name}"
        phone = helpers.generate_phone_no_for_sending_sms(_user.phone)
        random_pass = "".join(random.choice(string.digits) for _ in range(6))
        _user.password = make_password(random_pass)
        _user.save(update_fields=['password'])
        sms_text = "Dear {},\nYour account has been activated.Please log in with following credential.\nPhone: {},\nPassword: {}\nKeep using HealthOS and get exciting offers.".format(
            full_name, _user.phone, random_pass
        )
        # Sending sms to client
        send_sms.delay(
            phone,
            sms_text,
            _user.organization_id
        )

    def perform_update(self, serializer):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        offer_rules = self.request.data.get('offer_rules', [])
        referrer_id = self.request.data.get('referrer', None)
        primary_responsible_person_id = self.request.data.get(
            'primary_responsible_person', None)
        secondary_responsible_person_id = self.request.data.get(
            'secondary_responsible_person', None)
        update_data = {
            'updated_by_id': self.request.user.id
        }
        if offer_rules and is_distributor:
            update_data['offer_rules'] = offer_rules

        # if referrer_id:
        #     update_data['referrer_id'] = referrer_id

        # if 'primary_responsible_person_id' in self.request.data:
        #     update_data['primary_responsible_person_id'] = primary_responsible_person_id

        # if 'secondary_responsible_person_id' in self.request.data:
        #     update_data['secondary_responsible_person_id'] = secondary_responsible_person_id

        serializer.save(**update_data)
        is_registration_approval = helpers.to_boolean(
            self.request.data.get('registration_approval', False)
        )
        organization_user_id = self.request.data.get(
            'organization_user_id', None)

        # Update delivery hub for person and person organization
        organization_id = serializer.data.get("id", None)
        delivery_hub_id = serializer.data.get("delivery_hub", None)
        # Update related persons delivery hub
        Person().get_all_actives().filter(
            organization_id=organization_id
        ).update(delivery_hub_id=delivery_hub_id)
        # Update related person organization delivery hub
        PersonOrganization().get_all_actives().filter(organization_id=organization_id).update(
            delivery_hub_id=delivery_hub_id
        )
        # Approve ecommerce self registration
        if is_registration_approval and organization_user_id and serializer.instance.type == OrganizationType.DISTRIBUTOR_BUYER:
            self.approve_registration(organization_user_id)
            # publish all the public banner for the organization
            public_messages = PopUpMessage().get_all_actives().filter(
                is_public=True
            ).values("id")

            # Convert the queryset to a list of dictionaries
            published_messages_data = [
                {
                    "message_id": message["id"],
                    "organization": self.get_object(),
                    "entry_by": self.request.user,
                    "publish_date": timezone.now(),
                }
                for message in public_messages
            ]

            # Bulk create PublishedPopUpMessage objects
            PublishedPopUpMessage.objects.bulk_create([
                PublishedPopUpMessage(**data) for data in published_messages_data
            ])

        # user_id = str(format(self.request.user.id, '06d'))
        # organization_id = str(format(self.request.user.organization_id, '04d'))
        # key_organization_setting = 'organization_setting_{}-{}'.format(organization_id, user_id)
        # cache.delete(key_organization_setting)


class OrganizationInsights(generics.ListAPIView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDistributionT3,
        StaffIsSalesManager,
    )
    queryset = Organization().get_all_actives()

    permission_classes = (CheckAnyPermission,)

    def get(self, request, *args, **kwargs):
        organization_alias = kwargs.get("alias", None)
        organization = Organization().get_all_actives().only("id").filter(
            alias=organization_alias
        ).first()

        if not organization:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)

        # Call the utils method to get the organization order summary
        organization_insights = get_organization_order_insights(organization_id=organization.id)

        return Response(organization_insights, status=status.HTTP_200_OK)


class PersonAccessOrganizationList(generics.ListAPIView):
    serializer_class = OrganizationModelSerializer.Lite
    permission_classes = (AnyLoggedInUser,)
    # def get_queryset(self):
    #     queryset = PersonOrganization.objects.filter(
    #         status=Status.ACTIVE,
    #         person__alias=self.kwargs['person_alias']
    #     ).values_list('organization__id', flat=True)

    #     organizations = Organization.objects.filter(
    #         status=Status.ACTIVE,
    #         pk__in=queryset,
    #     ).order_by('pk')
    #     return organizations
    # Changed the property value for matching with organization search API
    def get(self, request, person_alias):
        keyword = self.request.query_params.get('keyword', '')
        exclude_person_groups = [
            PersonGroupType.REFERRER,
            PersonGroupType.PATIENT,
            PersonGroupType.PRESCRIBER
        ]
        queryset = PersonOrganization.objects.filter(
            status=Status.ACTIVE,
            person__alias=person_alias
        ).exclude(
            person_group__in=exclude_person_groups
        ).values('organization__id').annotate(
            id=F('organization__id'),
            name=F('organization__name'),
            primary_mobile=F('organization__primary_mobile'),
            address=F('organization__address'),
            person_group=F('person_group'),
            alias=F('alias'),
            status=F('organization__status'),
        )
        if keyword:
            queryset = queryset.filter(organization__name__icontains=keyword)

        return Response(queryset)


class SupplierList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = SupplierBasicSerializer

    def get_queryset(self):
        return Person.objects.filter(
            person_group=PersonGroupType.SUPPLIER,
            organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).order_by('pk')


class SupplierDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = SupplierBasicSerializer
    queryset = Person.objects.filter(
        person_group=PersonGroupType.SUPPLIER, status=Status.ACTIVE)
    lookup_field = 'alias'


class PorterFromReporterCreate(ListCreateAPICustomView):
    serializer_class = PersonModelSerializer.PorterCreateSerializer

    def get_queryset(self):
        return Person.objects.filter(
            person_group=PersonGroupType.EMPLOYEE,
            organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).order_by('-id')


class UserPhoneNumberUpdate(generics.UpdateAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsTelemarketer,
        IsSuperUser,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PersonModelSerializer.PhoneNumberUpdateOnlySerializer
    queryset = Person().get_all_actives()
    lookup_field = "alias"


class UserPasswordResetList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = UserPasswordResetListSerializer
    filterset_class = PasswordResetFilter

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = PasswordReset().get_all_actives().select_related(
            "user",
            "organization",
        )

        return queryset


class UserPasswordResetByCustomerCareService(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for resetting user passwords by customer care service.
        """
        password_reset_alias = self.kwargs.get('alias')

        try:
            # Attempt to retrieve a pending password reset request based on the alias
            password_reset = PasswordReset.objects.get(
                reset_status=ResetStatus.PENDING,
                type=ResetType.MANUAL,
                alias=password_reset_alias
            )
        except PasswordReset.DoesNotExist:
            # If no such request exists, return a 404 Not Found response
            return Response({
                "detail": "No pending request is available"
            }, status=status.HTTP_404_NOT_FOUND)

        user = password_reset.user

        # Generate a random password for the user and update it
        random_pass = "".join(random.choice(string.digits) for _ in range(6))
        user.password = make_password(random_pass)
        user.save(update_fields=['password'])

        # Prepare SMS context for the client
        url = "https://ecom.healthosbd.com"
        phone_number = generate_phone_no_for_sending_sms(user.phone)
        full_name = "{} {}".format(user.first_name, user.last_name)
        sms_text = "Dear {},\nPlease go to {} and login with the following credentials:\nPhone: {},\nPassword: {}.".format(
            full_name, url, user.phone, random_pass
        )
        healthos_sms_text = """Password reset successful, \nPharmacy Name: {}, \nUser: {}, \nMobile: {}
                    """.format(user.organization.name, full_name, phone_number)

        # Sending an SMS to the client asynchronously
        send_sms.delay(
            phone_number,
            sms_text,
            user.organization.id
        )

        # Send a message to a Slack or Mattermost channel asynchronously
        send_message_to_slack_or_mattermost_channel_lazy.delay(
            os.environ.get('HOS_PASSWORD_RESET_REQUEST_CHANNEL_ID', ""),
            healthos_sms_text
        )

        # Update the password reset status to indicate success
        password_reset.reset_status = ResetStatus.SUCCESS
        password_reset.save(update_fields=['reset_status'])

        return Response({"message": "Success"}, status=status.HTTP_200_OK)


class UserSoftDelete(APIView):
    available_permission_classes = (AnyLoggedInUser,)

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        user.status = Status.INACTIVE
        user.is_active = False
        user.save(update_fields=["status", "is_active"])
        return Response({
            "message": "Deletion Success"
        }, status=status.HTTP_204_NO_CONTENT)
