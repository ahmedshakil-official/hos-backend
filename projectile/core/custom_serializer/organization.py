'''
Move following serializer on this page:
<class 'core.serializers.OrganizationDetailsSerializer'>
<class 'core.serializers.OrganizationSerializer'>
'''
from rest_framework import serializers
from rest_framework.serializers import Serializer
from rest_framework.serializers import (
    ValidationError
)

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.custom_serializer_field import UUIDRelatedField

from common.validators import validate_phone_number
from common.enums import Status
from common.json_validator_schemas import geo_location_schema

from core.custom_serializer.delivery_hub import DeliveryHubNameCodeLiteSerializer
from core.models import Organization, PersonOrganization, DeliveryHub, Area
from core.enums import PersonGroupType, OrganizationType
from .person import PersonModelSerializer
from .area import AreaModelSerializer

from django_json_field_schema_validator.validators import JSONFieldSchemaValidator

from core.custom_serializer.area import AreaModelSerializer


class OrganizationMeta(ListSerializer.Meta):
    model = Organization
    fields = ListSerializer.Meta.fields + (
        'status',
        'name',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class OrganizationModelSerializer:

    class Lite(ListSerializer):
        '''
        This serializer will be used to get limited data of Organization
        '''
        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'primary_mobile',
                'address',
                'delivery_thana',
                'delivery_sub_area',
            )

    class Short(ListSerializer):
        '''
        This serializer will be used to get organization info for creating task log
        '''
        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'address',
                'contact_person',
                'primary_mobile',
            )

    class LiteWithGeoLocation(ListSerializer):
        """
        This serializer will be used to get limited data of Organization
        """
        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                "primary_mobile",
                "address",
                "delivery_thana",
                "delivery_sub_area",
                "geo_location",
            )

    class LiteForDistributorStockProductList(ListSerializer):
        '''
        This serializer will be used to get limited data of Organization for DistributorSalesAbleStockProductList
        '''
        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'order_ending_time',
            )


    class LiteWithEntryBy(ListSerializer):
        '''
        This serializer will be used to get limited data of Organization with entry by
        '''
        entry_by = PersonModelSerializer.EntryBy(read_only=True)

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'primary_mobile',
                'address',
                'entry_by',
                'delivery_thana',
                'active_issue_count',
                'delivery_sub_area',
            )


    class LiteWithResponsiblePerson(ListSerializer):
        '''
        This serializer will be used to get limited data of Organization with Primary Responsible Person
        '''
        primary_responsible_person = PersonModelSerializer.EntryBy(required=False, read_only=True)

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'primary_mobile',
                'address',
                'primary_responsible_person',
                'delivery_thana',
                'active_issue_count',
                'delivery_sub_area',
                'geo_location',
            )


    class InvoicePDF(ListSerializer):
        '''
        This serializer will be used to get limited data of Organization with Primary Responsible Person
        '''
        primary_responsible_person = PersonModelSerializer.EntryBy(required=False, read_only=True)
        area = AreaModelSerializer.NameOnly(read_only=True)

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'primary_mobile',
                'address',
                'primary_responsible_person',
                'delivery_thana',
                'delivery_sub_area',
                'area',
            )


    class LiteWithMinOrderAmount(ListSerializer):
        '''
        This serializer will be used to get min order amount for organization
        '''

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'min_order_amount',
            )

    class Post(ListSerializer):
        '''
        This serializer will be used to list, create, update Organization
        '''
        primary_mobile = serializers.CharField(
            allow_null=False, validators=[validate_phone_number])
        other_contact = serializers.CharField(
            allow_null=True, default=None, validators=[validate_phone_number])
        entry_by = PersonModelSerializer.EntryBy(required=False, read_only=True)
        # referrer = PersonModelSerializer.EntryBy(required=False, read_only=True)
        area = serializers.SlugRelatedField(
            queryset=Area().get_all_non_inactives(),
            slug_field="alias",
            error_messages={
                "detail": "Area does not exist.",
            },
            write_only=True
        )

        def get_copies_while_print(self, obj):
            try:
                labels = obj.copies_while_print.split(',')
                return [{'label': item.upper(), 'name': item} for item in labels if item]
            except AttributeError:
                return []

        def validate_type(self, value):
            request = self.context.get('request')
            if (request.user.person_group == PersonGroupType.TRADER and \
                value == OrganizationType.DISTRIBUTOR_BUYER) or request.user.is_superuser:
                return value
            elif request.method != 'POST':
                return value
            raise ValidationError(
                'YOU_DO_NOT_HAVE_PERMISSION_TO_CREATE_THIS_TYPE_OF_ORGANIZATION')


        def validate(self, data):
            request = self.context.get('request')
            name = data.get("name")
            primary_mobile = data.get("primary_mobile")

            if request.method == 'POST':
                existing_organizations = Organization().get_all_actives().filter(
                    name=name,
                    primary_mobile=primary_mobile
                )
                if existing_organizations.exists():
                    raise serializers.ValidationError(
                        'THE_ORGANIZATION_NAME_MUST_BE_UNIQUE_WITH_PRIMARY_MOBILE')

            return data


        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                # 'mother',
                'primary_mobile',
                'other_contact',
                'type',
                # 'slogan',
                'address',
                'contact_person',
                'contact_person_designation',
                'email',
                # 'website',
                # 'domain',
                'logo',
                # 'name_font_size',
                # 'slogan_font_size',
                # 'print_slogan',
                # 'print_address',
                # 'print_logo',
                # 'print_header',
                # 'print_patient_code',
                # 'print_patient_group',
                # 'show_label_transaction_print',
                # 'show_label_consumed_print',
                # 'show_label_sales_print',
                # 'show_label_appointment_print',
                'copies_while_print',
                # 'show_global_product',
                # 'transaction_receipt_note',
                'license_no',
                'license_image',
                'created_at',
                'entry_by',
                'delivery_hub',
                'delivery_thana',
                'delivery_sub_area',
                'min_order_amount',
                'referrer',
                'primary_responsible_person',
                'secondary_responsible_person',
                "discount_factor",
                "area",
                "has_dynamic_discount_factor",
            )
            read_only_fields = OrganizationMeta.read_only_fields + (
                'created_at',
                'entry_by',
            )


    class List(ListSerializer):
        '''
        This serializer will be used to list, create, update Organization
        '''

        primary_mobile = serializers.CharField(
            allow_null=False, validators=[validate_phone_number])
        other_contact = serializers.CharField(
            allow_null=True, default=None, validators=[validate_phone_number])
        entry_by = PersonModelSerializer.EntryBy(required=False, read_only=True)
        referrer = PersonModelSerializer.EntryBy(required=False, read_only=True)
        primary_responsible_person = PersonModelSerializer.EntryBy(required=False, read_only=True)
        secondary_responsible_person = PersonModelSerializer.EntryBy(required=False, read_only=True)
        delivery_hub = DeliveryHubNameCodeLiteSerializer(required=False, read_only=True)

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                # 'mother',
                'primary_mobile',
                'other_contact',
                'type',
                # 'slogan',
                'address',
                'contact_person',
                'contact_person_designation',
                'email',
                # 'website',
                # 'domain',
                'logo',
                # 'name_font_size',
                # 'slogan_font_size',
                # 'print_slogan',
                # 'print_address',
                # 'print_logo',
                # 'print_header',
                # 'print_patient_code',
                # 'print_patient_group',
                # 'show_label_transaction_print',
                # 'show_label_consumed_print',
                # 'show_label_sales_print',
                # 'show_label_appointment_print',
                'copies_while_print',
                'show_global_product',
                # 'transaction_receipt_note',
                'license_no',
                'license_image',
                'created_at',
                'entry_by',
                'delivery_hub',
                'delivery_thana',
                'delivery_sub_area',
                'min_order_amount',
                'referrer',
                'primary_responsible_person',
                'secondary_responsible_person',
            )
            read_only_fields = OrganizationMeta.read_only_fields + (
                'created_at',
                'entry_by',
            )

    class ListForDeliveryMan(ListSerializer):
        '''
        This serializer will be used to list for delivery man
        '''

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                'primary_mobile',
                'address',
                'delivery_thana',
                'delivery_sub_area',
                'name',
                'last_order_date',
                'last_month_order_amount',
                'this_month_order_amount',
            )
            read_only_fields = OrganizationMeta.read_only_fields + ()

    class Details(ListSerializer):
        '''
        This serializer will be used to see details of Organization
        '''
        entry_by = PersonModelSerializer.EntryBy(read_only=True)
        referrer = PersonModelSerializer.EntryBy(required=False, read_only=True)
        primary_responsible_person = PersonModelSerializer.EntryBy(required=False, read_only=True)
        secondary_responsible_person = PersonModelSerializer.EntryBy(required=False, read_only=True)
        offer_rules = serializers.JSONField()
        delivery_hub = DeliveryHubNameCodeLiteSerializer(required=False, read_only=True)
        area = AreaModelSerializer.List()

        class Meta(OrganizationMeta):
            fields = OrganizationMeta.fields + (
                # 'mother',
                'primary_mobile',
                'other_contact',
                'type',
                # 'slogan',
                'address',
                'contact_person',
                'contact_person_designation',
                'email',
                # 'website',
                # 'domain',
                'logo',
                # 'name_font_size',
                # 'slogan_font_size',
                # 'print_slogan',
                # 'print_address',
                # 'print_logo',
                # 'print_header',
                # 'print_patient_code',
                # 'print_patient_group',
                # 'show_label_transaction_print',
                # 'show_label_consumed_print',
                # 'show_label_sales_print',
                # 'show_label_appointment_print',
                'copies_while_print',
                # 'show_global_product',
                # 'transaction_receipt_note',
                'license_no',
                'license_image',
                'entry_by',
                'delivery_thana',
                'delivery_hub',
                'delivery_sub_area',
                'min_order_amount',
                'offer_rules',
                'referrer',
                'primary_responsible_person',
                'secondary_responsible_person',
                "discount_factor",
                "area",
                "has_dynamic_discount_factor",
            )

    class WriteForBulkUpdate(ListSerializer):
        # query is increasing for selecting the following fields, rest of the field are being called by super save method.
        alias = UUIDRelatedField(
            # fields=('id', 'alias', 'referrer', 'primary_responsible_person', 'secondary_responsible_person'),
        )
        referrer = UUIDRelatedField(
            model=PersonOrganization,
            required=False,
        )
        primary_responsible_person = UUIDRelatedField(
            model=PersonOrganization,
            required=False,
        )
        secondary_responsible_person = UUIDRelatedField(
            model=PersonOrganization,
            required=False,
        )

        class Meta(OrganizationMeta):
            fields = (
                'alias',
                'referrer',
                'primary_responsible_person',
                'secondary_responsible_person',
                "discount_factor",
                "has_dynamic_discount_factor",
            )

    class LocationOnly(ListSerializer):
        geo_location = serializers.JSONField(validators=[JSONFieldSchemaValidator(geo_location_schema)])
        max_distance = serializers.IntegerField(
            default=0,
            required=False,
            write_only=True,
            min_value=1,
            max_value=10,
        )

        class Meta(OrganizationMeta):
            fields = (
                'alias',
                'geo_location',
                'max_distance',
            )

    class GeoLocationOnly(ListSerializer):
        """
            This serializer will be used to get organization name and geolocation info list
        """

        class Meta(OrganizationMeta):
            fields = ("name", 'geo_location')


class DistributorBuyerOrganizationMergeSerializer(Serializer):
    """
    Serializer for DistributorBuyerOrganizationMerge view.
    """
    clone_organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.exclude(status=Status.INACTIVE),
        required=True
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.exclude(status=Status.INACTIVE),
        required=True
    )
