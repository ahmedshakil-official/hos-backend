import json
from django.contrib.auth import authenticate, login, logout
from django.db.models import Prefetch, Q
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenViewBase,
)
from rest_framework_simplejwt.tokens import RefreshToken
from common.enums import (Status, )
from common.tasks import cache_write_lazy
from core.enums import PersonGroupType, OrganizationType
from ..serializers import (
    PersonSerializer,
    PersonBasicSerializer,
    MeLoginSerializer,
)
from ..custom_serializer.jwt import TokenObtainPairSerializer
from ..models import Person, PersonOrganization, Organization


class UserProfileDetail(APIView):
    exclude_person_groups = [
        PersonGroupType.REFERRER,
        PersonGroupType.PATIENT,
        PersonGroupType.PRESCRIBER
    ]
    def get_key(self):
        return self.request.user.get_user_profile_details_cache_key()

    def get(self, request, format=None):
        person_data = cache.get(self.get_key())
        timeout = 604800 # 7 days (7*24*60*60)
        if person_data is not None:
            return Response(person_data)
        person = Person.objects.prefetch_related(
            Prefetch(
                'person_organization',
                queryset=PersonOrganization.objects.filter(
                    status=Status.ACTIVE,
                    organization__id=request.user.organization_id,
                    person_group=self.request.user.person_group,
                    person__id=request.user.id
                ).exclude(person_group__in=self.exclude_person_groups).select_related(
                    'default_storepoint',
                ).only(
                    'id',
                    'alias',
                    'default_storepoint__id',
                    'default_storepoint__alias',
                    'default_storepoint__name',
                    'first_name',
                    'last_name',
                    # 'allow_back_dated_transaction',
                )
            )
        ).select_related(
            'organization'
        ).only(
            'id',
            'alias',
            'status',
            'email',
            'phone',
            'first_name',
            'last_name',
            'last_login',
            'profile_image',
            'hero_image',
            'language',
            'theme',
            'person_group',
            'company_name',
            'is_superuser',
            'is_staff',
            'pagination_type',
            # 'date_picker',
            'code',
            # 'is_positive',
            # 'show_generic_name',
            # 'show_group_name',
            # 'show_subgroup_name',
            # 'show_item_in_one_line',
            'organization__name',
            'organization__status',
            'organization__alias',
            # 'organization__mother',
            'organization__primary_mobile',
            'organization__other_contact',
            'organization__type',
            # 'organization__slogan',
            'organization__address',
            'organization__contact_person',
            'organization__contact_person_designation',
            'organization__email',
            # 'organization__website',
            # 'organization__domain',
            'organization__logo',
            # 'organization__name_font_size',
            # 'organization__slogan_font_size',
            # 'organization__print_slogan',
            # 'organization__print_address',
            # 'organization__print_logo',
            # 'organization__print_header',
            # 'organization__print_patient_code',
            # 'organization__print_patient_group',
            # 'organization__show_label_transaction_print',
            # 'organization__show_label_consumed_print',
            # 'organization__show_label_sales_print',
            # 'organization__show_label_appointment_print',
            'organization__copies_while_print',
            'organization__show_global_product',
            # 'organization__transaction_receipt_note',
            'organization__license_no',
            'organization__license_image',
            'organization__created_at',
            'organization__entry_by',
            'organization__delivery_thana',
            'organization__min_order_amount',
            'organization__delivery_sub_area',
            'organization__delivery_hub__name',
            'organization__delivery_hub__short_code',
        ).get(id=request.user.id, status=Status.ACTIVE,)
        serializer = PersonSerializer(person, context={"request":request})
        response_data = serializer.data
        cache_data = json.loads(json.dumps(response_data, cls=DjangoJSONEncoder))
        cache_write_lazy.apply_async(
            args=(self.get_key(), cache_data, timeout),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        return Response(response_data)

    def put(self, request, format=None):
        serializer = PersonSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):

            phone = serializer.validated_data.get("phone", "")
            otp = serializer.validated_data.get("otp", None)
            if (phone and request.user.phone != phone and
                    request.user.organization.id != 303 and otp is None):
                # Return a response indicating that OTP will be sent to the user's phone
                return Response({
                    "detail": "OTP has sent to your phone number.",
                    "code": "OTP"
                }, status=status.HTTP_200_OK)

            serializer.save()
            return Response(serializer.data)

    def patch(self, request):
        serializer = PersonBasicSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):

            phone = serializer.validated_data.get("phone", "")
            otp = serializer.validated_data.get("otp", None)
            if (phone and request.user.phone != phone and
                    request.user.organization.id != 303 and otp is None):
                # Return a response indicating that OTP will be sent to the user's phone
                return Response({
                    "detail": "OTP has sent to your phone number.",
                    "code": "OTP"
                }, status=status.HTTP_200_OK)

            serializer.save()
            person_organization_instance = PersonOrganization.objects.filter(
                status=Status.ACTIVE,
                organization=request.user.organization,
                person=request.user.id
            ).exclude(person_group__in=self.exclude_person_groups)
            if 'default_storepoint' in request.data:
                person_organization_instance.update(
                    default_storepoint=request.data['default_storepoint'])

            return Response(serializer.data)

class MeLogin(APIView):
    permission_classes = ()

    def post(self, request, format=None):
        serializer = MeLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = authenticate(
                username=serializer.data['phone'],
                password=serializer.data['password']
            )
            if user is not None:
                organization_data = Organization.objects.values(
                    'status',
                    'type',
                ).get(
                    pk=user.organization_id
                )
                organization_status = organization_data.get('status')
                organization_type = organization_data.get('type')
                if organization_type != OrganizationType.DISTRIBUTOR and not user.is_superuser:
                    raise serializers.ValidationError('You have no access to login this site.')
                if organization_status == Status.INACTIVE:
                    person_organizations = PersonOrganization.objects.filter(
                        person__id=user.id,
                        organization__status=Status.ACTIVE,
                        person_group=user.person_group
                    ).only(
                        'id',
                        'organization',
                    ).order_by('-pk')
                    if person_organizations.exists():
                        organization_id = person_organizations.first().organization_id
                        user.organization_id = organization_id
                        user.save(update_fields=['organization'])

                if organization_status == Status.ACTIVE:
                    if user.is_active and user.status == Status.ACTIVE:
                        login(request, user)
                        return Response()
                    raise serializers.ValidationError('PLEASE_ACTIVATE_ACCOUNT')
                raise serializers.ValidationError('YOUR_ORGANIZATION_IS_INACTIVE')
            raise serializers.ValidationError('INVALID_LOGIN_CREDENTIALS')
        raise serializers.ValidationError('INVALID_LOGIN_CREDENTIALS')


class MeLogout(APIView):
    def post(self, request):
        try:
            logout(request)
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logout(request)
            return Response()


class TokenObtainPairCustomView(TokenViewBase):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = TokenObtainPairSerializer
