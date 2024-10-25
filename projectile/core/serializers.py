import re, difflib
from datetime import date, timedelta, datetime
from django.db.models.functions import Cast
from django.db.models import IntegerField
from django.db.models import Max
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.db import transaction, IntegrityError
from django.utils import timezone

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    HyperlinkedModelSerializer,
    ValidationError,
)

from common.enums import Status
from common.serializers import DynamicFieldsModelSerializer
from common.validators import (
    validate_unique_name_with_org,
    validate_uniq_supplier_with_org,
    validate_phone_number_person_group_wise,
    validate_phone_number,
    validate_unique_name,
    validate_phone_number_with_and_without_country_code,
)
from common.tasks import send_sms, send_message_to_slack_or_mattermost_channel_lazy
from common.utils import generate_map_url_and_address_from_geo_data
from common.helpers import generate_phone_no_for_sending_sms, to_boolean
from core.custom_serializer.delivery_hub import (
    DeliveryHubNameCodeLiteSerializer
)
from core.custom_serializer.organization import (
    OrganizationModelSerializer
)
from account.models import Accounts
from pharmacy.models import StorePoint

from .choices import OtpType

from .models import (
    Person,
    Department,
    EmployeeDesignation,

    PersonOrganization,

    ScriptFileStorage,
    AuthLog,
    OTP,
    PasswordReset,
    Area,
)
from .enums import (
    PersonGroupType,
    OrganizationType,
    Themes,
    LoginFailureReason,
    FilePurposes,
)
from .utils import getCountryCode, generate_unique_otp
from .custom_serializer.person import PersonModelSerializer


class PasswordResetSerializer(Serializer):
    """
    Serializer for requesting a password reset sms.
    """
    phone = serializers.CharField()
    password_reset_form_class = PasswordResetForm


class PasswordResetRequestSerializer(Serializer):
    """
    Serializer for requesting a password reset via slack.
    """
    mobile_no = serializers.CharField(required=True)
    pharmacy_name = serializers.CharField(required=True)


class PersonMinifiedLiteSerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias'
        )


class StorepointForDefaultSettings(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = StorePoint
        fields = (
            'id',
            'alias',
            'name',
        )


class DefaultCashPointSerializer(ModelSerializer):

    class Meta:
        model = Accounts
        fields = (
            'id',
            'alias',
            'name'
        )


class PersonOrganizationUserProfileSerializer(ModelSerializer):
    default_storepoint = StorepointForDefaultSettings()

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'default_storepoint',
            'first_name',
            'last_name',
            # 'allow_back_dated_transaction',
        )


class DepartmentSerializer(ModelSerializer):
    # pylint: disable=old-style-class, no-init
    def validate_name(self, value):
        if validate_unique_name_with_org(self, value, Department):
            return value
        else:
            raise ValidationError(
                'YOU_HAVE_ALREADY_A_DEPARTMENT_WITH_SAME_NAME')

    class Meta:
        model = Department
        fields = (
            'id',
            'alias',
            'name',
            'description',
        )


class PersonBasicSerializer(ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    # pylint: disable=old-style-class, no-init
    phone = serializers.CharField(
        min_length=11, max_length=24,
        validators=[
            UniqueValidator(queryset=Person.objects.all()),
            validate_phone_number_with_and_without_country_code]
        )
    otp = serializers.CharField(
        required=False, allow_blank=True,
        allow_null=True, write_only=True
    )

    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'email',
            'first_name',
            'last_name',
            'dob',
            'phone',
            'full_name',
            'organization',
            'language',
            'theme',
            'person_group',
            'code',
            'pagination_type',
            'profile_image',
            'otp'
        )

    def validate(self, data):
        otp = data.get("otp", None)
        phone = data.get("phone", None)

        if (phone and self.instance.phone != phone
                and self.instance.organization.id != 303):

            if not otp:
                # Check if the user has an OTP created in the last 5 minutes
                five_minutes_ago = datetime.now() - timedelta(minutes=5)
                existing_otp = OTP.objects.filter(
                    user=self.instance,
                    created_at__gte=five_minutes_ago,
                    is_used=False,
                    type=OtpType.PHONE_NUMBER_RESET
                ).exists()
                if existing_otp:
                    # User already has a valid OTP created in the last 5 minutes
                    raise ValidationError({'detail': "You already have an OTP. Please wait for the message."})
                else:
                    otp = generate_unique_otp()
                    OTP.objects.create(
                        user=self.instance,
                        otp=otp,
                        type=OtpType.PHONE_NUMBER_RESET
                    )

                    # Sending sms
                    message = f"Your HealthOS OTP is {otp}, It's valid for 5 minutes."
                    phone_number = generate_phone_no_for_sending_sms(self.instance.phone)
                    send_sms.delay(phone_number, message, self.instance.organization_id)

            else:
                # Find the OTP record associated with the user and the provided OTP.
                try:
                    otp_record = OTP.objects.get(
                        user=self.instance,
                        otp=otp,
                        is_used=False,
                        type=OtpType.PHONE_NUMBER_RESET
                    )
                except OTP.DoesNotExist:
                    raise ValidationError({"detail": "Invalid OTP."})

                if timezone.now() < (otp_record.created_at + timedelta(minutes=5)):
                    # OTP is valid and not expired.
                    # Update the user's phone number.
                    self.instance.phone = phone
                    self.instance.save(update_fields=['phone'])
                    self.instance.organization.primary_mobile = phone
                    self.instance.organization.save(update_fields=['primary_mobile'])

                    # Update the otp status is used.
                    otp_record.is_used = True
                    otp_record.save(update_fields=['is_used'])

                else:
                    raise ValidationError({"detail": "OTP has expired."})

        return data


class PersonLiteSerializer(ModelSerializer):
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'email',
            'dob',
            'first_name',
            'last_name',
            'nid',
            'phone',
            # 'economic_status',
            'code',
            'gender',
        )


class PersonSerializer(HyperlinkedModelSerializer):
    profile_image = serializers.ImageField(read_only=True)
    hero_image = serializers.ImageField(read_only=True)
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    thumb_medium = serializers.ReadOnlyField(source='get_thumb_medium')
    thumb_large = serializers.ReadOnlyField(source='get_thumb_large')
    hero_image_thumb = serializers.ImageField(
        source='get_hero_image_thumbnail', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    organization = OrganizationModelSerializer.List(read_only=True)
    person_organization = PersonOrganizationUserProfileSerializer(many=True, read_only=True)
    otp = serializers.CharField(required=False, allow_blank=True,
                                allow_null=True, write_only=True)
    delivery_hub = DeliveryHubNameCodeLiteSerializer()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'status',
            'email',
            'phone',
            'first_name',
            'last_name',
            'full_name',
            'organization',
            'last_login',
            'profile_image',
            'hero_image',
            'thumb_small',
            'thumb_medium',
            'thumb_large',
            'hero_image_thumb',
            'language',
            'theme',
            'person_group',
            'company_name',
            'is_superuser',
            'is_staff',
            'pagination_type',
            'person_organization',
            'code',
            'current_date',
            'has_tagged_supplier',
            'has_tagged_contractor',
            'otp',
            'delivery_hub'
        )
        read_only_fields = (
            'id',
            'last_login',
        )

    def validate(self, data):
        otp = data.get("otp", None)
        phone = data.get("phone", None)
        phone_from_instance = phone if self.instance else ""

        org_from_instance = self.instance.organization.id if self.instance else ""

        if (phone and phone_from_instance != phone
                and org_from_instance != 303 and self.instance):
            # Check phone number already exists
            phone_exists = Person.objects.filter(phone=phone).exists()
            if phone_exists:
                raise ValidationError({'detail': 'This phone number is already exists'})

            if not otp:
                # Check if the user has an OTP created in the last 5 minutes
                five_minutes_ago = datetime.now() - timedelta(minutes=5)
                existing_otp = OTP.objects.filter(
                    user=self.instance,
                    created_at__gte=five_minutes_ago,
                    is_used=False,
                    type=OtpType.PHONE_NUMBER_RESET
                ).exists()
                if existing_otp:
                    # User already has a valid OTP created in the last 5 minutes
                    raise ValidationError({'detail': "You already have an OTP. Please wait for the message."})
                else:
                    otp = generate_unique_otp()
                    OTP.objects.create(
                        user=self.instance,
                        otp=otp,
                        type=OtpType.PHONE_NUMBER_RESET
                    )

                    # Sending sms
                    message = f"Your HealthOS OTP is {otp}, It's valid for 5 minutes."
                    phone_number = generate_phone_no_for_sending_sms(self.instance.phone)
                    send_sms.delay(phone_number, message, self.instance.organization.id)

            else:
                # Find the OTP record associated with the user and the provided OTP.
                try:
                    otp_record = OTP.objects.get(
                        user=self.instance,
                        otp=otp,
                        is_used=False,
                        type=OtpType.PHONE_NUMBER_RESET
                    )
                except OTP.DoesNotExist:
                    raise ValidationError({"detail": "Invalid OTP."})

                if timezone.now() < (otp_record.created_at + timedelta(minutes=5)):
                    # OTP is valid and not expired.
                    # Update the user's phone number.
                    self.instance.phone = phone
                    self.instance.save(update_fields=['phone'])

                    # Update the otp status is used.
                    otp_record.is_used = True
                    otp_record.save(update_fields=['is_used'])

                else:
                    raise ValidationError({"detail": "OTP has expired."})

        return data


class PersonOrganizationBasicSerializer(ModelSerializer):
    # pylint: disable=old-style-class, no-init

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'person',
            'organization',
            # 'duty_shift',
            'status',
        )


class PersonOrganizationBasicGetOrCreateSerializer(ModelSerializer):
    # pylint: disable=old-style-class, no-init

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'person',
            'organization',
            'status',
        )

    def get_unique_together_validators(self):
        '''
        Overriding method to disable unique together checks
        '''
        return []


class EmployeeSerializer(ModelSerializer):
    from core.custom_serializer.employee_designation import (
        EmployeeDesignationModelSerializer
    )
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    designation = EmployeeDesignationModelSerializer.Details()
    country_code = serializers.SerializerMethodField()
    person_organization = PersonOrganizationBasicSerializer(
        source="get_person_organization_for_employee")
    full_name = serializers.SerializerMethodField()
    employee_balance = serializers.FloatField(
        source='get_person_organization_balance_for_employee')
    delivery_hub = DeliveryHubNameCodeLiteSerializer(read_only=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'first_name',
            'full_name',
            'last_name',
            'designation',
            'registration_number',
            'degree',
            'joining_date',
            'dob',
            'gender',
            'email',
            'phone',
            'nid',
            # 'birth_id',
            'permanent_address',
            'present_address',
            'mothers_name',
            'fathers_name',
            # 'husbands_name',
            'balance',
            # 'remarks',
            'status',
            'profile_image',
            'thumb_small',
            'country',
            'country_code',
            'person_group',
            'person_organization',
            'employee_balance',
            'permissions',
            'delivery_hub',
        )

    def get_country_code(self, obj):
        return getCountryCode(obj.country)

    def get_full_name(self, obj):
        name = u"{} {}".format(obj.first_name, obj.last_name)
        return name.strip()


class ServiceProviderSerializer(ModelSerializer):
    from core.custom_serializer.employee_designation import (
        EmployeeDesignationModelSerializer
    )
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    designation = EmployeeDesignationModelSerializer.Details()
    full_name = serializers.CharField(source="get_full_name")

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'first_name',
            'full_name',
            'last_name',
            'designation',
            'registration_number',
            'degree',
            'joining_date',
            'dob',
            'gender',
            'email',
            'phone',
            'status',
            'profile_image',
            'thumb_small',
            'country',
            'person_group'
        )


class EmployeeSearchLiteSerializer(ModelSerializer):
    from core.custom_serializer.employee_designation import (
        EmployeeDesignationModelSerializer
    )
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    designation = EmployeeDesignationModelSerializer.Details()
    country_code = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    employee_balance = serializers.FloatField()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'first_name',
            'full_name',
            'last_name',
            'designation',
            'registration_number',
            'degree',
            'joining_date',
            'dob',
            'gender',
            'email',
            'phone',
            'nid',
            # 'birth_id',
            'permanent_address',
            'present_address',
            'mothers_name',
            'fathers_name',
            # 'husbands_name',
            'balance',
            # 'remarks',
            'status',
            'profile_image',
            'thumb_small',
            'country',
            'country_code',
            'person_group',
            'employee_balance',
        )

    def get_country_code(self, obj):
        return getCountryCode(obj.country)

    def get_full_name(self, obj):
        name = u"{} {}".format(obj.first_name, obj.last_name)
        return name.strip()


class EmployeeSearchSerializer(EmployeeSearchLiteSerializer):
    person_organization = PersonOrganizationBasicSerializer()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'first_name',
            'full_name',
            'last_name',
            'designation',
            'registration_number',
            'degree',
            'joining_date',
            'dob',
            'gender',
            'email',
            'phone',
            'nid',
            # 'birth_id',
            'permanent_address',
            'present_address',
            'mothers_name',
            'fathers_name',
            # 'husbands_name',
            'balance',
            # 'remarks',
            'status',
            'profile_image',
            'thumb_small',
            'country',
            'country_code',
            'person_group',
            'person_organization',
            'employee_balance',
        )


class EmployeeBasicSerializer(ModelSerializer):
    # GENDER_CHOICES = [
    #     PersonGender.MALE,
    #     PersonGender.FEMALE,
    #     PersonGender.TRANSSEXUAL
    # ]

    profile_image = serializers.ImageField(required=False)
    # make some fields required
    first_name = serializers.CharField(min_length=2, max_length=30)
    last_name = serializers.CharField(min_length=2, max_length=30)
    phone = serializers.CharField(
        min_length=10, max_length=24,
        validators=[
            UniqueValidator(queryset=Person.objects.all()),
            validate_phone_number])
    # gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    dob = serializers.DateField()
    designation = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeDesignation.objects.filter(status=Status.ACTIVE))
    manager = serializers.PrimaryKeyRelatedField(
        queryset=PersonOrganization.objects.exclude(status=Status.INACTIVE),
        required=False,
    )
    degree = serializers.CharField(min_length=2, max_length=256)
    password = serializers.CharField(style={'input_type': 'password'}, required=False)
    confirm_password = serializers.CharField(style={'input_type': 'password'}, required=False)
    delivery_hub = DeliveryHubNameCodeLiteSerializer(read_only=True)

    def validate_password(self, value):
        confirm_password = self.initial_data.get('confirm_password')
        if confirm_password and value:
            if confirm_password != value:
                raise ValidationError('Confirm password does not match!')
            validate_password(value)
            value = make_password(value)
        return value

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'status',
            'first_name',
            'last_name',
            'designation',
            'registration_number',
            'degree',
            'joining_date',
            'dob',
            'gender',
            'email',
            'phone',
            'nid',
            # 'birth_id',
            'balance',
            'permanent_address',
            'present_address',
            'mothers_name',
            'fathers_name',
            # 'husbands_name',
            # 'remarks',
            'profile_image',
            'country',
            'password',
            'confirm_password',
            'code',
            'manager',
            'delivery_hub',
        )
        read_only_fields = (
            'id',
        )

    def create(self, validated_data):
        request = self.context.get('request', None)
        allow_back_dated_transaction = request.data.get('allow_back_dated_transaction', '')
        manager = validated_data.pop('manager', None)
        try:
            password = validated_data.get('password')
            if not password:
                del validated_data['password']
            del validated_data['confirm_password']
        except KeyError:
            pass
        person = Person.objects.create(
            person_group=PersonGroupType.EMPLOYEE, **validated_data)
        person.save()
        if manager:
            person_organizations = PersonOrganization.objects.filter(
                person=person,
                organization__id=request.user.organization_id
            ).exclude(status=Status.INACTIVE)
            for person_organization in person_organizations:
                person_organization.manager = manager
                person_organization.save()
        return person


class SupplierBasicSerializer(PersonSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    # make some fields required
    phone = serializers.CharField(
        min_length=10,
        max_length=24,
        validators=[UniqueValidator(
            queryset=Person.objects.all()),
            validate_phone_number
        ])

    def validate_company_name(self, value):
        if validate_uniq_supplier_with_org(self, value, Person):
            return value
        else:
            raise ValidationError('YOU_HAVE_ALREADY_A_SUPPLIER_WITH_SAME_NAME')

    company_name = serializers.CharField(min_length=2)
    opening_balance = serializers.FloatField(min_value=0)

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'status',
            'phone',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'balance',
            'last_login',
            'company_name',
            'contact_person',
            'contact_person_number',
            'contact_person_address',
            'joining_date',
            'opening_balance',
        )
        read_only_fields = (
            'id',
            'last_login',
        )

    def create(self, validated_data):
        try:
            balance = validated_data['opening_balance']
        except KeyError:
            balance = 0
        person = Person.objects.create(
            balance=balance, person_group=PersonGroupType.SUPPLIER, **validated_data)
        person.save()
        return person


class PersonOrganizationSupplierSerializer(PersonSerializer):
    phone = serializers.CharField(
        min_length=10, max_length=24,
        validators=[
            UniqueValidator(queryset=Person.objects.all()),
            validate_phone_number]
    )

    def validate_company_name(self, value):
        if validate_uniq_supplier_with_org(self, value, PersonOrganization):
            return value
        else:
            raise ValidationError('YOU_HAVE_ALREADY_A_SUPPLIER_WITH_SAME_NAME')

    company_name = serializers.CharField(min_length=2)
    opening_balance = serializers.FloatField()
    code = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'phone',
            'email',
            'first_name',
            'last_name',
            'balance',
            'company_name',
            'contact_person',
            'contact_person_number',
            'contact_person_address',
            'joining_date',
            'opening_balance',
            'code'
        )
        read_only_fields = (
            'id',
        )

    def create(self, validated_data):
        code = validated_data.pop('code', None)

        codes = Person.objects.filter(person_group=PersonGroupType.SUPPLIER).values_list(
            'code', flat=True).exclude(code__isnull=True)

        max_code = 0
        for code_ in codes:
            max_code = max(max_code, int(code_))

        if code:
            if code == f"{max_code + 1:03}":
                pass
            else:
                raise ValidationError('Provided code is not sequentially correct')
        else:
            code = f"{max_code + 1:03}"

        try:
            balance = validated_data['opening_balance']
        except KeyError:
            balance = 0

        person = Person.objects.create(
            balance=balance, person_group=PersonGroupType.SUPPLIER, code=code, **validated_data)
        person.save()

        return person

    def update(self, instance, validated_data):
        code = validated_data.pop('code', instance.person.code)

        instance = super().update(instance, validated_data)

        codes = Person.objects.filter(person_group=PersonGroupType.SUPPLIER).values_list(
            'code', flat=True).exclude(code__isnull=True)

        max_code = 0
        for code_ in codes:
            max_code = max(max_code, int(code_))

        if code:
            if code == f"{max_code + 1:03}":
                pass
            elif code == instance.person.code:
                pass
            else:
                raise ValidationError('Provided code is not sequentially correct')
        else:
            code = f"{max_code + 1:03}"

        person = instance.person
        person.code = code
        person.save()

        instance.code = person.code
        instance.save()

        return instance


class PersonOrganizationSupplierGetSerializer(ModelSerializer):
    person = PersonMinifiedLiteSerializer()
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'phone',
            'email',
            'balance',
            'company_name',
            'contact_person',
            'contact_person_number',
            'contact_person_address',
            'joining_date',
            'opening_balance',
            'person',
        )


class ReferrerSerializer(ModelSerializer):
    full_name = serializers.SerializerMethodField()
    country_code = serializers.SerializerMethodField()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'phone',
            'first_name',
            'last_name',
            'full_name',
            'balance',
            'country',
            'country_code',
            'person_group'
        )

    def get_full_name(self, obj):
        name = u"{} {} - {}".format(obj.first_name, obj.last_name, obj.phone)
        return name.strip()

    def get_country_code(self, obj):
        return getCountryCode(obj.country)


# pylint: disable=old-style-class, no-init

class PersonOrganizationReferrerDetailsSerializer(ModelSerializer):
    from core.custom_serializer.employee_designation import (
        EmployeeDesignationModelSerializer
    )
    designation = EmployeeDesignationModelSerializer.Details()

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'phone',
            'first_name',
            'last_name',
            'balance',
            'country',
            'country_code',
            'person_group',
            # 'referrer_category',
            # 'referrer_organization',
            'organization_wise_serial',
            # 'area',
            'degree',
            'designation',
        )

class PersonOrganizationGetSerializer(ModelSerializer):
    # pylint: disable=old-style-class, no-init
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'code',
            'balance',
            # 'credit_limit',
            # 'appointment_schedules',
            # 'diagnosis_with',
        )


class ReferrerBasicSerializer(ModelSerializer):
    first_name = serializers.CharField(min_length=2, max_length=30)
    last_name = serializers.CharField(min_length=2, max_length=30)
    phone = serializers.CharField(
        min_length=10, max_length=24,
        validators=[
            UniqueValidator(queryset=Person.objects.all()),
            validate_phone_number
        ])
    opening_balance = serializers.FloatField(min_value=0)
    # referrer_category = serializers.ReadOnlyField()
    # referrer_organization = serializers.ReadOnlyField()
    # area = serializers.ReadOnlyField()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = Person
        fields = (
            'id',
            'alias',
            'phone',
            'first_name',
            'last_name',
            'opening_balance',
            'country',
            # 'referrer_category',
            # 'referrer_organization',
            # 'area',
        )

        read_only_fields = (
            'id',
        )

    def create(self, validated_data):
        request = self.context.get("request")
        balance = validated_data.pop('opening_balance', 0.00)
        referrer_category = request.data.get('referrer_category')
        referrer_organization = request.data.get('referrer_organization')
        area = request.data.get('area')
        person = Person.objects.create(
            person_group=PersonGroupType.REFERRER,
            balance=balance,
            **validated_data)
        person.save()
        if any([referrer_category, referrer_organization, area]):
            person_organization = PersonOrganization.objects.get(
                person_id=person.id, person_group=PersonGroupType.REFERRER)
            if referrer_category:
                person_organization.referrer_category_id = referrer_category
            if referrer_organization:
                person_organization.referrer_organization = referrer_organization
            if area:
                person_organization.area = area
            person_organization.save()
        return person


class MeLoginSerializer(Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, obj, validated_data):
        pass


class CountryListSerializer(Serializer):
    label = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_label(self, obj):
        return obj['label']

    def get_code(self, obj):
        return obj['code']

    def get_name(self, obj):
        return obj['name']

    def create(self, validated_data):
        pass

    def update(self, obj, validated_data):
        pass


class DateFormatSerializer(Serializer):
    name = serializers.SerializerMethodField()
    example = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj['name']

    def get_example(self, obj):
        return obj['example']

    def create(self, validated_data):
        pass

    def update(self, obj, validated_data):
        pass


class PersonOrganizationSerializer(ModelSerializer):
    # pylint: disable=old-style-class, no-init
    person = EmployeeSerializer()
    organization = OrganizationModelSerializer.List()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'person',
            'organization',
            'status',
        )


class PersonOrganizationDetailsSerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'person',
            'organization',
            'email',
            'phone',
            'code',
            'first_name',
            'last_name',
            'country_code',
            # 'economic_status',
            'permanent_address',
            'present_address',
            'dob',
            'gender',
            'fathers_name',
            'mothers_name',
            # 'husbands_name',
            # 'relatives_name',
            # 'relatives_relation',
            # 'relatives_contact_number',
            # 'duty_shift',
            'status',
        )


class PersonOrganizationLiteSerializer(DynamicFieldsModelSerializer):
    # pylint: disable=old-style-class, no-init
    person = PersonBasicSerializer()

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'person',
            'organization',
            # 'duty_shift',
            'first_name',
            'last_name',
            'company_name',
            'phone',
            'code',
            'contact_person_number',
            'contact_person_address',
        )


class PersonOrganizationEmployeeSerializer(ModelSerializer):
    from core.custom_serializer.employee_designation import (
        EmployeeDesignationModelSerializer
    )
    person = PersonMinifiedLiteSerializer()
    designation = EmployeeDesignationModelSerializer.Details()
    # pylint: disable=old-style-class, no-init

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'first_name',
            'last_name',
            'code',
            'designation',
            'phone',
            'status',
            'dob',
            'person',
            'person_group',
            'updated_at',
            'created_at',
        )
        ready_only_fields = (
            'id',
            'created_at',
        )

class PersonOrganizationEmployeeBasicSerializer(ModelSerializer):
    profile_image = serializers.ImageField(required=False)
    # make some fields required
    first_name = serializers.CharField(min_length=2, max_length=30)
    last_name = serializers.CharField(min_length=2, max_length=30)
    dob = serializers.DateField()
    designation = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeDesignation.objects.filter(status=Status.ACTIVE))
    degree = serializers.CharField(min_length=2, max_length=256)
    password = serializers.CharField(
        style={'input_type': 'password'}, allow_null=True, allow_blank=True, write_only=True)
    confirm_password = serializers.CharField(
        style={'input_type': 'password'}, allow_null=True, allow_blank=True, write_only=True)

    manager = serializers.PrimaryKeyRelatedField(
        queryset=PersonOrganization.objects.exclude(status=Status.INACTIVE),
        required=False,
    )


    def validate_password(self, value):
        confirm_password = self.initial_data.get('confirm_password')
        if confirm_password and value:
            if confirm_password != value:
                raise ValidationError('Confirm password does not match!')
            validate_password(value)
            value = make_password(value)
        return value

    def validate_phone(self, value):
        request = self.context.get("request")
        if validate_phone_number_person_group_wise(self, value, PersonGroupType.EMPLOYEE, request.user.organization)\
                and validate_phone_number(value):
            return value
        else:
            raise ValidationError(
                'PHONE_NUMBER_MUST_BE_UNIQUE')

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'status',
            'first_name',
            'last_name',
            'code',
            'designation',
            'registration_number',
            'degree',
            'joining_date',
            'dob',
            'gender',
            'email',
            'phone',
            'nid',
            'balance',
            'permanent_address',
            'present_address',
            'mothers_name',
            'fathers_name',
            'profile_image',
            'country',
            'password',
            'confirm_password',
            'default_storepoint',
            'manager',
            'tagged_supplier',
            'tagged_contractor',
            'delivery_hub',
        )
        read_only_fields = (
            'id',
        )

    def create(self, validated_data):
        if not validated_data['password']:
            del validated_data['password']
        del validated_data['confirm_password']
        employee = PersonOrganization.objects.create(
            person_group=PersonGroupType.EMPLOYEE, **validated_data)
        employee.save()
        return employee


class PersonOrganizationCommonSerializer(ModelSerializer):
    '''
    Person Organization common field serializer
    '''
    person = PersonMinifiedLiteSerializer()
    delivery_hub = DeliveryHubNameCodeLiteSerializer()

    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'first_name',
            'last_name',
            'phone',
            'email',
            'person_group',
            'code',
            'dob',
            'balance',
            # 'economic_status',
            'person',
            'company_name',
            'degree',
            # 'diagnosis_with',
            'present_address',
            'permissions',
            'delivery_hub',
        )


class PersonOrganizationEmployeeLiteSerializer(ModelSerializer):
    '''
    Person Organization employee basic serializer
    '''
    from core.custom_serializer.employee_designation import (
        EmployeeDesignationModelSerializer
    )
    designation = EmployeeDesignationModelSerializer.Details()
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'first_name',
            'last_name',
            'phone',
            'person_group',
            'degree',
            'code',
            'designation',
        )


class PersonOrganizationEmployeeSearchSerializer(ModelSerializer):
    '''
    Person Organization employee search serializer
    '''
    class Meta:
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'first_name',
            'last_name',
            'full_name',
            'person_group',
            'phone',
            'code',
        )


class ScriptFileStorageSerializer(ModelSerializer):

    def validate_content(self, content):
        import pandas as pd
        purchase_prediction_columns = [
            'ID',
            'MRP',
            'SP',
            'AVG',
            'L_RATE',
            'H_RATE',
            'KIND',
            'STATUS',
            'OSTOCK',
            'SELL',
            'PUR',
            'SHORT',
            'RET',
            'NSTOCK',
            'PRED',
            'NORDER',
            'D3',
            'SUPPLIER_S1',
            'QTY_S1',
            'RATE_S1',
            'SUPPLIER_S2',
            'QTY_S2',
            'RATE_S2',
            'SUPPLIER_S3',
            'QTY_S3',
            'RATE_S3'
        ]

        distributor_stock_columns = [
            'ID',
            'STOCK',
        ]
        request = self.context.get('request')
        file_purpose = request.data.get('file_purpose', '')
        set_stock_from_file = to_boolean(request.data.get('set_stock_from_file', False))
        missing_columns = []
        if validate_unique_name(self, content.name, ScriptFileStorage):
            if file_purpose and file_purpose == str(FilePurposes.PURCHASE_PREDICTION):
                data_frame = pd.read_excel(content)
                columns_from_file = data_frame.columns.to_list()
                necessary_columns = []
                for item in columns_from_file:
                    match = re.search("SUPPLIER_S", item)
                    if match:
                        for li in difflib.ndiff(item, "SUPPLIER_S"):
                            if li[0] == '-':
                                suggested_supplier = li[-1]
                                supplier_col_name = f"SUPPLIER_S{suggested_supplier}"
                                qty_col_name = f"QTY_S{suggested_supplier}"
                                rate_col_name = f"RATE_S{suggested_supplier}"
                                necessary_columns.append(supplier_col_name)
                                necessary_columns.append(qty_col_name)
                                necessary_columns.append(rate_col_name)
                purchase_prediction_columns += necessary_columns
                missing_columns = list(set(purchase_prediction_columns) - set(columns_from_file))
            elif file_purpose and file_purpose == str(FilePurposes.DISTRIBUTOR_STOCK) and set_stock_from_file:
                data_frame = pd.read_csv(content)
                columns_from_file = data_frame.columns.to_list()
                missing_columns = list(set(distributor_stock_columns) - set(columns_from_file))
            if missing_columns:
                raise ValidationError(
                    f"The file mush have columns: {', '.join(missing_columns)}"
                )

            return content
        else:
            raise ValidationError(
                'YOU_HAVE_ALREADY_A_FILE_WITH_SAME_NAME')

    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = ScriptFileStorage
        fields = (
            'id',
            'status',
            'alias',
            'date',
            'name',
            'content_type',
            'content',
            'purpose',
            'description',
            'set_stock_from_file',
            'file_purpose',
            'is_locked',
        )


class DistributorBuyerOrderSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    registration = serializers.DateField()
    order_number = serializers.IntegerField()
    amount = serializers.FloatField()
    first_order = serializers.DateField()
    last_order = serializers.DateField()
    registration_since = serializers.CharField()
    order_since = serializers.CharField()


class DistributorBuyerOrderHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    registered = serializers.DateField()
    primary_mobile = serializers.CharField()
    order_number = serializers.IntegerField()
    ordered_on_days = serializers.IntegerField()
    order_value = serializers.FloatField()
    last_order = serializers.DateField()
    last_order_days_ago = serializers.IntegerField()
    entry_by = PersonModelSerializer.EntryBy(read_only=True)

class OrganizationDataSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    license_no = serializers.CharField(required=False)
    delivery_thana = serializers.IntegerField()
    license_image = serializers.ImageField(required=False)


class UserDataSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(
        min_length=10, max_length=11,
        validators=[
            UniqueValidator(queryset=Person.objects.all()),
            validate_phone_number
        ]
    )
    profile_image = serializers.ImageField(required=False)


class EcommerceUserRegistrationSerializer(ModelSerializer):

    # organization_data = OrganizationDataSerializer()
    # user_data = UserDataSerializer()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(
        min_length=11, max_length=24,
        validators=[
            validate_phone_number_with_and_without_country_code]
    )
    profile_image = serializers.ImageField(required=False)
    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    license_no = serializers.CharField(required=False)
    delivery_thana = serializers.IntegerField(required=False, allow_null=True)
    license_image = serializers.ImageField(required=False)
    area = serializers.PrimaryKeyRelatedField(
        queryset = Area().get_all_actives(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    def send_sms_to_user_and_slack(self, request, organization_data, org_id):
        import os

        nl = '\n'
        user_sms_text = "Your registration request has been submitted, we will contact soon for completing further process.Keep using HealthOS and get exciting offers."
        user_phone = generate_phone_no_for_sending_sms(organization_data.get('primary_mobile'))
        # Sending sms to User
        send_sms.delay(
            user_phone,
            user_sms_text,
            org_id
        )
        map_address = generate_map_url_and_address_from_geo_data(request.headers)
        pharmacy_name = organization_data.get('name')
        user_name = organization_data.get('contact_person')
        mobile_no = organization_data.get('primary_mobile')
        address = organization_data.get('address')
        gps_address = map_address.get('address', 'Not Found')
        google_map_url = map_address.get('map_url', 'Not Found')
        healthos_sms_text = f"New registration request received, {nl}Pharmacy Name: {pharmacy_name}, {nl}User Name: {user_name},{nl}Mobile No: {mobile_no}, {nl}Address: {address}, {nl}GPS Location: {gps_address}, {nl}Google Map: {google_map_url}"
        # Send message to slack channel
        send_message_to_slack_or_mattermost_channel_lazy.delay(
            os.environ.get("HOS_REGISTRATION_REQUEST_CHANNEL_ID", ""),
            healthos_sms_text
        )


    def create(self, validated_data):
        from core.models import Organization
        from common.cache_keys import DUPLICATE_USER_CREATION_CACHE_KEY_PREFIX
        from django.core.cache import cache

        # get the area from validated data
        area = validated_data.pop("area", None)
        phone = validated_data.get('phone')
        cache_key = f"{DUPLICATE_USER_CREATION_CACHE_KEY_PREFIX}{phone}"

        try:
            with transaction.atomic():
                request = self.context.get('request')
                organization_data = {
                    'status': Status.DRAFT,
                    'name': validated_data.get('name'),
                    'address': validated_data.get('address'),
                    "delivery_thana": area.code if area else validated_data.get("delivery_thana"),
                    "area": area if area else None,
                    'license_no': validated_data.get('license_no'),
                    'license_image': validated_data.get('license_image'),
                    # 'slogan': 'Friend of Pharmacy',
                    'primary_mobile': validated_data.get('phone'),
                    'contact_person': f"{validated_data.get('first_name')} {validated_data.get('last_name')}",
                    'type': OrganizationType.DISTRIBUTOR_BUYER,
                }

                organization_instance = Organization.objects.create(
                    **organization_data
                )

                user_data = {
                    'first_name': validated_data.get('first_name'),
                    'last_name':validated_data.get('last_name'),
                    'phone':validated_data.get('phone'),
                    'profile_image':validated_data.get('profile_image', None),
                    'person_group': PersonGroupType.EMPLOYEE,
                    'theme': Themes.LIGHT,
                    'organization': organization_instance
                }
                user_instance = Person.objects.create(
                    **user_data
                )
                user_instance.save()
                organization_instance.entry_by = user_instance
                organization_instance.save()
                user_instance.refresh_from_db()
                user_instance.entry_by_id = user_instance.id
                user_instance.save(update_fields=['entry_by'])

                if user_instance and organization_instance:
                    self.send_sms_to_user_and_slack(
                        request,
                        organization_data,
                        organization_instance.id
                    )
                return validated_data
        except IntegrityError:
            if cache_key.get(cache_key):
                cache.delete(cache_key)
            return None

    class Meta:
        model = Person
        fields = (
            'first_name',
            'last_name',
            'phone',
            'profile_image',
            'name',
            'address',
            'license_no',
            'delivery_thana',
            'license_image',
            "area",
        )


class AuthFailureLogSerializer(ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'}, allow_null=True, allow_blank=True, write_only=True)

    def validate_password(self, value):
        if value:
            value = make_password(value)
        return value

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = AuthLog
        fields = (
            'phone',
            'password',
            'error_message'
        )

    def create(self, validated_data):
        password = validated_data.get('password', '')
        phone = validated_data.get('phone', '')
        failure_reason = LoginFailureReason.OTHERS
        entry_by = None
        try:
            user = Person.objects.get(
                status=Status.ACTIVE,
                person_group=PersonGroupType.EMPLOYEE,
                phone=phone
            ).only('password')
            is_valid_password = check_password(
                password,
                user.password
            )
            if not is_valid_password:
                failure_reason = LoginFailureReason.WRONG_PASSWORD
            entry_by = user
        except Person.DoesNotExist:
            failure_reason = LoginFailureReason.INVALID_USER
        except Person.MultipleObjectsReturned:
            pass
        auth_log = AuthLog.objects.create(
            entry_by=entry_by,
            failure_reason=failure_reason,
            **validated_data
        )
        return auth_log


class UserPasswordResetSerializer(ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = (
            "id",
            "alias",
            "status",
        )
        read_only_fields = ("id", "alias", "status")


class UserPasswordResetListSerializer(UserPasswordResetSerializer):
    user = PersonLiteSerializer(read_only=True)
    organization = OrganizationModelSerializer.Lite(read_only=True)
    date = serializers.DateTimeField(source="created_at", read_only=True)
    class Meta(UserPasswordResetSerializer.Meta):
        fields = UserPasswordResetSerializer.Meta.fields + (
            "user",
            "organization",
            "phone",
            "reset_status",
            "type",
            "date",
            "reset_date"
        )
        read_only_fields = UserPasswordResetSerializer.Meta.read_only_fields + ()


class OrganizationNetSalesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    mobile = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
