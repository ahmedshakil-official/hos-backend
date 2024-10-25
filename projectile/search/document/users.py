import json
from django.db.models import Value
from django.db.models.functions import Concat
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from common.enums import Status
from core.models import (
    Department,
    Person,
    EmployeeDesignation,
    Organization,
    PersonOrganization,
)

from ..fields import CustomDateField
from ..indexes import get_index
from common.helpers import prepare_es_populate_filter as es_filter


@registry.register_document
class DepartmentDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()


    class Index:
        name = get_index('core_department')._name


    class Django:
        model = Department
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(DepartmentDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)

@registry.register_document
class PersonOrganizationDocument(Document):
    status = fields.IntegerField()
    # tag = fields.TextField(fields={'raw': fields.KeywordField()})
    first_name = fields.TextField(fields={'raw': fields.KeywordField()})
    last_name = fields.TextField(fields={'raw': fields.KeywordField()})
    full_name = fields.TextField(fields={'raw': fields.KeywordField()})
    email = fields.TextField(fields={'raw': fields.KeywordField()})
    phone = fields.TextField()
    code = fields.TextField(fields={'raw': fields.KeywordField()})
    gender = fields.IntegerField()
    dob = CustomDateField()
    # diagnosis_with = fields.TextField()
    balance = fields.DoubleField()
    # appointment_schedules = fields.TextField()
    # country = fields.TextField()
    country_code = fields.TextField()
    organization_wise_serial = fields.IntegerField()
    person = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'email' : fields.TextField(fields={'raw': fields.KeywordField()}),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'full_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'dob': CustomDateField(),
        'phone': fields.TextField(),
        # 'code': fields.TextField(),
        'theme':  fields.IntegerField(),
        'person_group': fields.IntegerField(),
        'language': fields.TextField(),
        'organization': fields.ObjectField(properties={
            'pk': fields.IntegerField(),
        })
    })
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField(),
    })
    alias = fields.TextField()
    person_group = fields.IntegerField()
    person_type =  fields.IntegerField()
    # duty_shift = fields.ObjectField(properties={
    #     'pk': fields.IntegerField()
    # })
    # dropout_status = fields.IntegerField()
    designation = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
        'department': fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'description': fields.TextField(),
        })
    })
    alias = fields.TextField()
    company_name = fields.TextField()
    contact_person = fields.TextField()
    # economic_status = fields.IntegerField()
    degree = fields.TextField()
    manager = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'person_group': fields.IntegerField(),
        'phone': fields.TextField(),
        'code': fields.TextField(),
    })

    permissions = fields.TextField()

    delivery_hub = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'short_code': fields.TextField(),
    })


    class Index:
        name = get_index('core_person_organization')._name


    class Django:
        model = PersonOrganization
        fields = [
            'id',
            'opening_balance'
        ]
        queryset_pagination = 1000
        # rebuild_from_value_list = True

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(PersonOrganizationDocument, self).get_queryset().select_related(
            'person',
            'person__organization',
            'organization',
            # 'duty_shift',
            'designation',
            'designation__department',
            # 'referrer_category',
        ).only(
            # 'status',
            # 'first_name',
            # 'last_name',
            # 'email',
            # 'phone',
            # 'code',
            # 'gender',
            # 'dob',
            # 'balance',
            # 'appointment_schedules',
            # 'country_code',
            # 'fingerprint_1',
            # 'fingerprint_2',
            # 'fingerprint_3',
            # 'organization_wise_serial',
            # 'diagnosis_with',
            # 'person',
            #     'person__id',
            #     'person__alias',
            #     'person__email',
            #     'person__first_name',
            #     'person__last_name',
            #     'person__dob',
            #     'person__phone',
            #     'person__theme',
            #     'person__person_group',
            #     'person__language',
            #     'person__organization',
            #         'person__organization__pk',
            # 'organization',
            #     'organization__id',
            # 'alias',
            # 'person_group',
            # 'person_type',
            # 'duty_shift',
            #     'duty_shift__id',
            # 'dropout_status',
            # 'designation',
            #     'designation__id',
            #     'designation__name',
            #     'designation__description',
            #     'designation__department',
            #         'designation__department__id',
            #         'designation__department__name',
            #         'designation__department__description',
            # 'company_name',
            # 'contact_person',
            # 'opening_balance',
            # 'economic_status',
            # 'referrer_category',
            #     'referrer_category__id',
            #     'referrer_category__alias',
            #     'referrer_category__name',
        ).filter(
            status__in=[Status.ACTIVE, Status.DRAFT]
        ).filter(
            **filters
        ).order_by(*orders)

    # def get_list(self, filters={}):
    #     return PersonOrganization.objects.values(
    #         'pk',
    #         'id',
    #         'status',
    #         'first_name',
    #         'last_name',
    #         'email',
    #         'phone',
    #         'code',
    #         'gender',
    #         'dob',
    #         'balance',
    #         'appointment_schedules',
    #         'country_code',
    #         'fingerprint_1',
    #         'fingerprint_2',
    #         'fingerprint_3',
    #         'organization_wise_serial',
    #         'diagnosis_with',
    #         'person',
    #             'person__id',
    #             'person__alias',
    #             'person__email',
    #             'person__first_name',
    #             'person__last_name',
    #             'person__dob',
    #             'person__phone',
    #             'person__theme',
    #             'person__person_group',
    #             'person__language',
    #             'person__organization',
    #                 'person__organization__id',
    #         'organization',
    #             'organization__id',
    #         'alias',
    #         'person_group',
    #         'person_type',
    #         'duty_shift',
    #             'duty_shift__id',
    #         'dropout_status',
    #         'designation',
    #             'designation__id',
    #             'designation__name',
    #             'designation__description',
    #             'designation__department',
    #                 'designation__department__id',
    #                 'designation__department__name',
    #                 'designation__department__description',
    #         'company_name',
    #         'contact_person',
    #         'opening_balance',
    #         'economic_status',
    #         'referrer_category',
    #             'referrer_category__id',
    #             'referrer_category__alias',
    #             'referrer_category__name',
    #     ).filter(status__in=[Status.ACTIVE, Status.DRAFT]).filter(**filters).annotate(
    #         full_name=Concat('first_name',
    #                          Value(' '), 'last_name')
    #     )


@registry.register_document
class EmployeeDesignationDocument(Document):
    department = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'description': fields.TextField()
    })
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    is_global = fields.IntegerField()
    alias = fields.TextField()

    class Index:
        name = get_index('core_employee_designation')._name


    class Django:
        model = EmployeeDesignation
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(EmployeeDesignationDocument, self).get_queryset().select_related(
            'organization',
            'department',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class OrganizationDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    # mother = fields.ObjectField(properties={
    #     'pk': fields.IntegerField()
    # })
    type = fields.IntegerField()
    status = fields.IntegerField()
    alias = fields.TextField()
    primary_mobile = fields.TextField(fields={'raw': fields.KeywordField()})
    created_at = CustomDateField()
    entry_by = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
    })
    referrer = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
    })
    primary_responsible_person = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
    })
    secondary_responsible_person = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
    })
    delivery_thana = fields.IntegerField()
    min_order_amount = fields.FloatField()
    delivery_sub_area = fields.TextField()
    # This fields are unnecessary now, we be removed permanently in future
    # last_order_date = CustomDateField(attr="last_order_date")
    # last_month_order_amount = fields.DoubleField(
    #     attr="last_month_order_amount"
    # )
    # this_month_order_amount = fields.DoubleField(
    #     attr="this_month_order_amount"
    # )

    class Index:
        name = get_index('core_organization')._name


    class Django:
        model = Organization
        fields = [
            'id',
            'address',
            'other_contact',
            'contact_person',
            'contact_person_designation',
            'email',
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super().get_queryset().select_related(
            'entry_by',
            'referrer',
            'primary_responsible_person',
            'secondary_responsible_person',
        ).filter(
            **filters
        ).order_by(*orders)
