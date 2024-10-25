'''
Move following serializer on this page:
<class 'core.serializers.EmployeeBasicSerializer'>
<class 'core.serializers.EmployeeSearchSerializer'>
<class 'core.serializers.EmployeeSerializer'>
<class 'core.serializers.EmployeeSupplierSearchSerializer'>
<class 'core.serializers.PatientSearchSerializer'>
<class 'core.serializers.PersonSerializer'>
<class 'core.serializers.ReferrerBasicSerializer'>
<class 'core.serializers.ReferrerSerializer'>
<class 'core.serializers.StackHolderSerializer'>
<class 'core.serializers.SupplierBasicSerializer'>
'''
from datetime import date
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.helpers import populate_es_index
from common.validators import (
    validate_phone_number,
    validate_phone_number_with_and_without_country_code
)
from common.enums import Status

from ..enums import PersonGroupType
from ..models import Person, PersonOrganization, EmployeeDesignation, Organization


# pylint: disable=old-style-class, no-init
class PersonMeta(ListSerializer.Meta):
    model = Person
    fields = ListSerializer.Meta.fields + (
        'first_name',
        'last_name',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class PersonModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to list Person model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(PersonMeta):
            pass

    class EntryBy(ListSerializer):
        '''
        This serializer will be used to get entry by of Person model
        '''
        class Meta(PersonMeta):
            fields = PersonMeta.fields + (
                'phone',
                'code',
            )

    class DistributorBuyerUserCredential(ListSerializer):
        '''
        This serializer will be used to user of distributor buyer for resetting credential
        '''
        class Meta(PersonMeta):
            fields = PersonMeta.fields + (
                'alias',
                'phone',
            )

    class PorterCreateSerializer(serializers.ModelSerializer):
        profile_image = serializers.ImageField(required=False)
        first_name = serializers.CharField(min_length=2, max_length=30)
        last_name = serializers.CharField(min_length=2, max_length=30)
        phone = serializers.CharField(
            min_length=10,
            max_length=24,
            validators=[
                UniqueValidator(queryset=Person.objects.all()),
                validate_phone_number,
            ],
        )
        dob = serializers.DateField()
        manager = serializers.PrimaryKeyRelatedField(
            queryset=PersonOrganization.objects.exclude(status=Status.INACTIVE),
            required=False,
        )

        # pylint: disable=old-style-class, no-init
        class Meta(PersonMeta):
            # model = Person
            fields = (
                "id",
                "alias",
                "first_name",
                "last_name",
                "degree",
                "dob",
                "gender",
                "email",
                "phone",
                "profile_image",
                "code",
                "manager",
            )
            read_only_fields = ("id", "alias")

        def create(self, validated_data):
            request = self.context["request"]
            designation = EmployeeDesignation.objects.filter(
                status=Status.ACTIVE, name__icontains="porter"
            ).first()

            validated_data["joining_date"] = date.today()
            validated_data["designation"] = designation
            manager = validated_data.pop("manager", None)
            person = Person.objects.create(
                person_group=PersonGroupType.EMPLOYEE, **validated_data
            )
            if validated_data.get("password", None):
                person.set_password(validated_data["password"])
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

    class PhoneNumberUpdateOnlySerializer(ListSerializer):
        phone = serializers.CharField(
            min_length=11,
            max_length=24,
            validators=[
                UniqueValidator(queryset=Person().get_all_non_inactives()),
                validate_phone_number,
            ],
        )
        primary_mobile = serializers.CharField(
            min_length=10,
            max_length=24,
            validators=[
                validate_phone_number,
            ],
            allow_null=True,
            allow_blank=True,
            required=False,
            write_only=True,
        )

        class Meta(PersonMeta):
            fields = PersonMeta.fields + (
                "phone",
                "primary_mobile",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
                "first_name",
                "last_name",
            )

        def update(self, instance, validated_data):
            """
                Update the person's phone numbers, including primary_mobile.

                This method updates the phone numbers for a person, including their organization primary_mobile number. It also checks if
                the primary_mobile number is unique among organizations and updates the Elasticsearch index accordingly.

                Args:
                    instance: The person instance to update.
                    validated_data: The validated data with updated phone numbers.

                Returns:
                    Updated person instance.
            """
            user = self.context.get("request").user
            validated_data["updated_by_id"] = user.id
            primary_mobile_number = validated_data.pop("primary_mobile", None)

            # If primary mobile number is provided then update organization primary mobile number
            if primary_mobile_number:
                # Check if another organization with the same primary mobile number exists
                organization_exists = Organization().get_all_non_inactives().filter(
                    primary_mobile=primary_mobile_number
                ).exclude(
                    id=instance.organization_id
                )

                if organization_exists:
                    # Raise a validation error if a conflicting organization exists
                    raise serializers.ValidationError(
                        {"primary_mobile": "This field must be unique."}
                    )

                # Update the primary mobile number for the organization
                Organization.objects.filter(
                    id=instance.organization_id
                ).update(
                    primary_mobile=primary_mobile_number
                )

                # Update the Elasticsearch index for the updated organizations
                populate_es_index(
                    'core.models.Organization',
                    {'id__in': [instance.organization_id]},
                )

            return super().update(instance, validated_data)
