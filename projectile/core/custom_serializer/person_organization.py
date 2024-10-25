'''
Move following serializer on this page:
<class 'core.serializers.PersonOrganizationBasicGetOrCreateSerializer'>
<class 'core.serializers.PersonOrganizationBasicSerializer'>
<class 'core.serializers.PersonOrganizationCommonSerializer'>
<class 'core.serializers.PersonOrganizationDeadPatientSearchSerializer'>
<class 'core.serializers.PersonOrganizationDetailsSerializer'>
<class 'core.serializers.PersonOrganizationEmployeeSearchSerializer'>
<class 'core.serializers.PersonOrganizationEmployeeSerializer'>
<class 'core.serializers.PersonOrganizationReferrerSerializer'>
<class 'core.serializers.PersonOrganizationSearchSerializer'>
<class 'core.serializers.PersonOrganizationSerializer'>
<class 'core.serializers.PersonOrganizationSupplierSerializer'>
'''


import contextlib
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.serializers import (
    ModelSerializer,
    ValidationError,
)
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from common.validators import (
    validate_phone_number_person_group_wise,
    validate_phone_number, validate_phone_number_with_and_without_country_code,
)
from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from common.enums import Status
from core.enums import PersonGroupType, Themes
from core.custom_serializer.delivery_hub import (
    DeliveryHubNameCodeLiteSerializer
)
from core.custom_serializer.employee_designation import (
    EmployeeDesignationModelSerializer
)

from ..models import PersonOrganization, Person
from ..serializers import PersonMinifiedLiteSerializer, PersonOrganizationSupplierGetSerializer


class ServiceConsumptionSerializer(ModelSerializer):

    class Meta:
        model = PersonOrganization
        fields = [
            'id',
            'alias',
            'phone',
            'code',
            'first_name',
            'last_name',
            'dob',
            'gender',
            'person_group',
        ]


class PersonOrganizationMeta(ListSerializer.Meta):
    model = PersonOrganization
    fields = ListSerializer.Meta.fields + (
        'first_name',
        'last_name',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # we can add readonly field here
    )


class PersonOrganizationBaseSerializer:

    class MinimalList(ListSerializer):
        """
        Get list of person organization minimal data
        """
        class Meta(PersonOrganizationMeta):
            # new field will be increase database query
            fields = PersonOrganizationMeta.fields + (
                'person_group',
                'phone',
                'code',
                'email',
            )

    class PrescriberList(ListSerializer):
        """
        Get list of prescriber data
        """
        designation = EmployeeDesignationModelSerializer.List()
        class Meta(PersonOrganizationMeta):
            # new field will be increase database query
            fields = PersonOrganizationMeta.fields + (
                'phone',
                'designation',
                'group_permission',
            )

    class PrescriberBasic(ListSerializer):
        """
        To update prescriber data
        """
        profile_image = serializers.ImageField(required=False)

        def validate_phone(self, value):
            if validate_phone_number_person_group_wise(self, value, PersonGroupType.PRESCRIBER)\
                    and validate_phone_number(value):
                return value
            else:
                raise ValidationError('PHONE_NUMBER_MUST_BE_UNIQUE')

        class Meta(PersonOrganizationMeta):
            fields = PersonOrganizationMeta.fields + (
                'phone',
                'person_type',
                'person_group',
                'designation',
                'degree',
                'dob',
                'gender',
                'email',
                'balance',
                'person',
                'joining_date',
                'registration_number',
                'permanent_address',
                'present_address',
                # 'remarks',
                'nid',
                # 'birth_id',
                'profile_image',
                'country',
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
                'person',
            )

    class PrescriberDetails(ListSerializer):
        """
        To get details of prescriber
        """
        designation = EmployeeDesignationModelSerializer.List()
        referrer = serializers.SerializerMethodField()
        class Meta(PersonOrganizationMeta):
            fields = PersonOrganizationMeta.fields + (
                'phone',
                'person_type',
                'person_group',
                'designation',
                'degree',
                'dob',
                'gender',
                'email',
                'balance',
                'person',
                'joining_date',
                'registration_number',
                'permanent_address',
                'present_address',
                # 'remarks',
                'nid',
                # 'birth_id',
                'profile_image',
                'country',
                'referrer',
            )

        def get_referrer(self, obj):
            try:
                referrer = PersonOrganization.objects.get(
                    person_group=PersonGroupType.REFERRER,
                    status__in=[Status.ACTIVE, Status.DRAFT],
                    person=obj.person,
                    organization=obj.organization
                )
                return {
                    'referrer_category': {
                        'id': referrer.referrer_category.id,
                        'name': referrer.referrer_category.name,
                        'alias': referrer.referrer_category.alias,
                    },
                    'referrer_organization': referrer.referrer_organization,
                    'area': referrer.area,
                }
            except (PersonOrganization.DoesNotExist, PersonOrganization.MultipleObjectsReturned):
                return {}


class PersonOrganizationModelSerializer(PersonOrganizationBaseSerializer):
    class EmployeeList(ListSerializer):
        from core.custom_serializer.employee_designation import (
            EmployeeDesignationModelSerializer
        )

        manager = PersonOrganizationBaseSerializer.MinimalList()
        person = PersonMinifiedLiteSerializer()
        designation = EmployeeDesignationModelSerializer.Details()
        delivery_hub=DeliveryHubNameCodeLiteSerializer(read_only=True)

        class Meta(PersonOrganizationMeta):
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
                'manager',
                'delivery_hub',
                'permissions'
            )
            ready_only_fields = (
                'id',
                'created_at',
                'permissions',
            )

    class EmployeeSearch(ListSerializer):
        from core.custom_serializer.employee_designation import (
            EmployeeDesignationModelSerializer
        )

        manager = PersonOrganizationBaseSerializer.MinimalList()
        person = PersonMinifiedLiteSerializer()
        designation = EmployeeDesignationModelSerializer.Details()
        delivery_hub = DeliveryHubNameCodeLiteSerializer()

        class Meta(PersonOrganizationMeta):
            fields = (
                'id',
                'alias',
                'first_name',
                'last_name',
                'code',
                'email',
                'designation',
                'phone',
                'status',
                'dob',
                'person',
                'person_group',
                'manager',
                'permissions',
                'delivery_hub',
            )
            ready_only_fields = (
            )

class TraderBasicSerializer(ModelSerializer):
    profile_image = serializers.ImageField(required=False)
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    # make some fields required
    phone = serializers.CharField(
        min_length=10,
        max_length=24,
        validators=[
            UniqueValidator(
                queryset=Person.objects.filter(~Q(person_group=PersonGroupType.EMPLOYEE))),
            validate_phone_number]
        )

    balance = serializers.FloatField(min_value=0, required=False, default=0.0)
    opening_balance = serializers.FloatField(required=False, default=0.0, allow_null=True)
    password = serializers.CharField(style={'input_type': 'password'}, required=False)
    confirm_password = serializers.CharField(style={'input_type': 'password'}, required=False)

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
        model = PersonOrganization
        fields = (
            'id',
            'alias',
            'phone',
            'email',
            'first_name',
            'last_name',
            'balance',
            'opening_balance',
            'gender',
            # 'area',
            'present_address',
            'permanent_address',
            'password',
            'confirm_password',
            'profile_image',
            'thumb_small',
            'status',
        )
        read_only_fields = (
            'id',
            'alias',
        )

    def create(self, validated_data):
        request = self.context.get('request', None)
        existing_person = request.data.get('existing_person', None)
        try:
            password = validated_data.get('password')
            if not password:
                del validated_data['password']
            del validated_data['confirm_password']
        except KeyError:
            pass
        area = validated_data.pop('area', '')
        balance = validated_data.pop('opening_balance', '')
        try:
            opening_balance = validated_data['balance']
        except KeyError:
            opening_balance = 0
        # If existing user available only create the person organization instance
        if existing_person:
            try:
                _password = validated_data.pop('password', '')
                person = Person.objects.get(pk=existing_person)
                PersonOrganization.objects.create(
                    person=person,
                    opening_balance=opening_balance,
                    person_group=PersonGroupType.TRADER,
                    area=area,
                    **validated_data
                )
                if _password:
                    person.password = _password
                    person.save(update_fields=['password'])
            except Person.DoesNotExist:
                pass
        else:
            person = Person.objects.create(
                opening_balance=opening_balance,
                person_group=PersonGroupType.TRADER,
                **validated_data
            )
            person.save()
        if any([area]) and not existing_person:
            person_organization = PersonOrganization.objects.get(
                person_id=person.id,
                organization=request.user.organization,
                person_group=PersonGroupType.TRADER
            )
            if area:
                person_organization.area = area
            person_organization.save()
        return person


class ContractorMeta(ListSerializer.Meta):
    model = PersonOrganization
    fields = ListSerializer.Meta.fields + (
        "code",
        "first_name",
        "last_name",
        "email",
        "gender",
        "present_address",
        "permanent_address",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()


class ContractorSerializer:
    class List(ListSerializer):
        thumb_small = serializers.ReadOnlyField(source="get_thumb_small")

        class Meta(ContractorMeta):
            fields = ContractorMeta.fields + (
                "phone",
                "balance",
                "opening_balance",
                "profile_image",
                "thumb_small",
                "status",
            )
            read_only_fields = ContractorMeta.read_only_fields + ()

    class Post(ListSerializer):
        profile_image = serializers.ImageField(required=False)
        phone = serializers.CharField(
            min_length=11, max_length=24,
            validators=[
                UniqueValidator(queryset=Person().get_all_non_inactives()),
                validate_phone_number_with_and_without_country_code]
        )
        balance = serializers.FloatField(min_value=0, required=False, default=0.0)
        opening_balance = serializers.FloatField(
            required=False, default=0.0, allow_null=True
        )
        password = serializers.CharField(
            style={"input_type": "password"}, write_only = True, required=False
        )
        confirm_password = serializers.CharField(
            style={"input_type": "password"}, write_only = True, required=False
        )

        def validate_password(self, value):
            confirm_password = self.initial_data.get("confirm_password")
            if confirm_password and value:
                if confirm_password != value:
                    raise ValidationError("Confirm password does not match!")
                validate_password(value)
                value = make_password(value)
            return value

        class Meta(ContractorMeta):
            fields = ContractorMeta.fields + (
                "phone",
                "balance",
                "status",
                "opening_balance",
                "password",
                "confirm_password",
                "profile_image",
            )
            read_only_fields = ContractorMeta.read_only_fields + ()

        def create(self, validated_data):

            request = self.context.get("request", None)
            existing_person = request.data.get("existing_person", None)

            with contextlib.suppress(KeyError):
                password = validated_data.get("password")
                if not password:
                    del validated_data["password"]
                del validated_data["confirm_password"]
            area = validated_data.pop("area", "")
            balance = validated_data.pop("opening_balance", "")

            try:
                opening_balance = validated_data["balance"]
            except KeyError:
                opening_balance = 0

            # if status is given Draft the set is_active = False
            is_active = (
                not validated_data.get("status", None)
                or validated_data.get("status") != Status.DRAFT
            )

            # If existing user available only create the person organization instance
            if existing_person:
                with contextlib.suppress(Person.DoesNotExist):
                    _password = validated_data.pop("password", "")
                    person = Person().get_all_actives().get(pk=existing_person)
                    PersonOrganization.objects.create(
                        person=person,
                        opening_balance=opening_balance,
                        person_group=PersonGroupType.CONTRACTOR,
                        area=area,
                        **validated_data
                    )
                    if _password:
                        person.password = _password
                        person.save(update_fields=["password"])
            else:
                person = Person.objects.create(
                    opening_balance=opening_balance,
                    person_group=PersonGroupType.CONTRACTOR,
                    is_active=is_active,
                    **validated_data
                )
                person.save()
            if any([area]) and not existing_person:
                person_organization = (
                    PersonOrganization()
                    .get_all_actives()
                    .get(
                        person_id=person.id,
                        organization=request.user.organization,
                        person_group=PersonGroupType.CONTRACTOR,
                    )
                )
                if area:
                    person_organization.area = area
                person_organization.save()
            return person

    class Update(ListSerializer):
        profile_image = serializers.ImageField(required=False)
        phone = serializers.CharField(
            min_length=11, max_length=24,
            validators=[
                UniqueValidator(queryset=Person.objects.exclude(status=Status.INACTIVE)),
                validate_phone_number]
        )
        balance = serializers.FloatField(min_value=0, required=False, default=0.0)
        opening_balance = serializers.FloatField(
            required=False, default=0.0, allow_null=True
        )
        password = serializers.CharField(style={'input_type': 'password'}, required=False, write_only=True)
        confirm_password = serializers.CharField(style={'input_type': 'password'}, required=False)

        def validate_password(self, value):
            confirm_password = self.initial_data.get('confirm_password')
            if confirm_password and value:
                if confirm_password != value:
                    raise ValidationError('Confirm password does not match!')
                validate_password(value)
                value = make_password(value)
            return value

        class Meta(ContractorMeta):
            fields = ContractorMeta.fields + (
                "phone",
                "balance",
                "status",
                "opening_balance",
                "profile_image",
                "password",
                "confirm_password",
            )
            read_only_fields = ContractorMeta.read_only_fields + ()


class DistributorBuyerUserCreateSerializer(ModelSerializer):
    """ This serializer will use to create distributor buyer credential
    """
    profile_image = serializers.ImageField(required=False)
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    # make some fields required
    phone = serializers.CharField(
        min_length=10,
        max_length=24,
        validators=[UniqueValidator(
            queryset=Person().get_all_actives()), validate_phone_number])

    balance = serializers.FloatField(min_value=0, required=False, default=0.0)
    opening_balance = serializers.FloatField(required=False, default=0.0, allow_null=True)
    # password = serializers.CharField(
    #     style={'input_type': 'password'}, allow_null=True, allow_blank=True, write_only=True)
    # confirm_password = serializers.CharField(
    #     style={'input_type': 'password'}, allow_null=True, allow_blank=True, write_only=True)

    # def validate_password(self, value):
    #     confirm_password = self.initial_data.get('confirm_password')
    #     if confirm_password and value:
    #         if confirm_password != value:
    #             raise ValidationError('Confirm password does not match!')
    #         validate_password(value)
    #         value = make_password(value)
    #     return value


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
            'opening_balance',
            'gender',
            # 'password',
            # 'confirm_password',
            'profile_image',
            'thumb_small',
        )
        read_only_fields = (
            'id',
            'alias',
        )

    def create(self, validated_data):
        # if not validated_data['password']:
        #     del validated_data['password']
        # del validated_data['confirm_password']
        try:
            opening_balance = validated_data['balance']
        except KeyError:
            opening_balance = 0
        person = Person.objects.create(
            person_group=PersonGroupType.EMPLOYEE,
            theme=Themes.LIGHT,
            **validated_data
        )
        person.save()
        return person


class PersonOrganizationEmployeeDetailsSerializer(PersonOrganizationModelSerializer.EmployeeList):
    thumb_small = serializers.ReadOnlyField(source='get_thumb_small')
    manager = PersonOrganizationModelSerializer.MinimalList()
    tagged_supplier = PersonOrganizationSupplierGetSerializer()
    tagged_contractor = PersonOrganizationSupplierGetSerializer()
    delivery_hub = DeliveryHubNameCodeLiteSerializer()

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
            'person',
            'person_group',
            'registration_number',
            'joining_date',
            'degree',
            'email',
            'country',
            'dob',
            'gender',
            'nid',
            'balance',
            'permanent_address',
            'present_address',
            'mothers_name',
            'fathers_name',
            'thumb_small',
            'profile_image',
            # 'remarks',
            'default_storepoint',
            'manager',
            'permissions',
            'tagged_supplier',
            'tagged_contractor',
            'delivery_hub',
        )
