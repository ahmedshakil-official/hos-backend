import logging, os
from dotmap import DotMap
from datetime import date
from validator_collection import checkers
from django.core.cache import cache

from common.cache_keys import ORDER_ENDING_TIME_CACHE, USER_PROFILE_DETAILS_CACHE_KEY_PREFIX
from .models import Organization, Person
logger = logging.getLogger(__name__)

def update_organization_responsible_person(organization_id, responsible_employee_id):
    from core.tasks import update_organization_responsible_person_on_bg

    update_organization_responsible_person_on_bg.apply_async(
        (organization_id, responsible_employee_id),
        countdown=5,
        retry=True, retry_policy={
            'max_retries': 10,
            'interval_start': 0,
            'interval_step': 0.2,
            'interval_max': 0.2,
        }
    )


def update_organization_responsible_employee(organization_id, responsible_employee_id):
    from common.helpers import custom_elastic_rebuild
    from core.models import Organization
    from pharmacy.enums import OrderTrackingStatus
    from common.enums import Status
    from ecommerce.models import OrderInvoiceGroup

    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    invoices = OrderInvoiceGroup.objects.filter(
        organization_id=distributor_id,
        order_by_organization_id=organization_id,
        status=Status.ACTIVE,
    ).values('id', 'delivery_date').exclude(
        current_order_status__in=[
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED
        ]
    ).order_by('-delivery_date').distinct('delivery_date')[0:3]

    # check if all three are done by this responsible_employee_id
    responsible_employee_id = None
    if len(invoices) == 3:
        employees = list(invoices.values_list('responsible_employee_id', flat=True))
        if employees[0] == employees[1] and employees[1] == employees[2]:
            responsible_employee_id = employees[0]

    # update organization responsible employee
    if responsible_employee_id is not None:
        organization_instance = Organization.objects.only(
            'primary_responsible_person_id').filter(
            pk=organization_id
        )
        organization_instance.update(
            primary_responsible_person_id=responsible_employee_id
        )
        custom_elastic_rebuild(
            'core.models.Organization',
            {'id': organization_id}
        )
        logger.info(
            f"Updated primary responsible employee id {responsible_employee_id} for organization {organization_id}"
        )


def get_organizations_by_area(organization):
    from core.models import Organization

    area = organization.get('delivery_thana', None)
    org_id = organization.get('id', '')
    if not area:
        return []
    return list(Organization().get_all_non_inactives().filter(
        delivery_thana=area
    ).exclude(pk=org_id).values(
        'id',
        'name',
        'delivery_sub_area',
        'primary_mobile',
        'contact_person',
        'address',
    ))

def get_matching_ratio(first, second):
    # import jellyfish
    from difflib import SequenceMatcher

    return round(SequenceMatcher(a=first.lower(), b=second.lower()).ratio() * 100, 2)
    # return round(jellyfish.jaro_distance(first.lower(), second.lower()) * 100, 2)

def fix_stop_words(name):
    stop_words = ['pharma', 'pharmacy',]
    name = name.split()
    name = [word for word in name if word.lower() not in stop_words]
    return ' '.join(name)


def get_order_ending_time():
    ending_time = cache.get(ORDER_ENDING_TIME_CACHE)
    if ending_time is not None and checkers.is_time(ending_time):
        return ending_time
    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    timeout = 86400
    try:
        settings = Organization.objects.only('id').get(pk=distributor_id).get_settings()
        ending_time = settings.order_ending_time
        cache.set(ORDER_ENDING_TIME_CACHE, ending_time, timeout)
        return ending_time
    except:
        return "09:00:00"


def update_organization_responsible_employee_from_invoices(invoice_groups):
    from collections import defaultdict

    from common.helpers import populate_es_index
    from .models import Organization, PersonOrganization

    invoices_group_by_organization = defaultdict(list)
    for invoice_group in invoice_groups:
        organization_id = invoice_group['order_by_organization']
        invoices_group_by_organization[organization_id].append(invoice_group)

    invoices_minimum_three_deliveries = {
        organization: invoice_group for organization, invoice_group in invoices_group_by_organization.items() if
        len(invoice_group) >= 3
    }
    invoices_res_emp_by_org = defaultdict(lambda: None)
    for organization, invoice_groups in invoices_minimum_three_deliveries.items():
        employees = []
        for invoice_group in invoice_groups:
            employees.append(invoice_group['responsible_employee'])
        if len(employees) >= 3:
            for index in range(len(employees) - 2):
                if employees[index] == employees[index + 1] and employees[index + 1] == employees[index + 2]:
                    invoices_res_emp_by_org[organization] = employees[index]
                    break

    organization_keys = list(invoices_res_emp_by_org.keys())
    organizations = Organization.objects.filter(id__in=organization_keys).values(
        'id',
        'primary_responsible_person'
    )

    obj_to_be_updated = []
    organization_ids = []
    for org in organizations:
        if org['primary_responsible_person'] != invoices_res_emp_by_org[org['id']]:
            obj_to_be_updated.append(
                Organization(
                    id=org["id"],
                    primary_responsible_person=PersonOrganization.objects.get(
                        pk=invoices_res_emp_by_org[org["id"]]
                    )
                )
            )
            organization_ids.append(org["id"])

    Organization.objects.bulk_update(
        obj_to_be_updated,
        ['primary_responsible_person'],
        batch_size=100
    )
    populate_es_index(
        'core.models.Organization',
        {'id__in': organization_ids},
    )

    return organization_ids

def get_user_profile_details_from_cache(user_id):
    cache_key = f"{USER_PROFILE_DETAILS_CACHE_KEY_PREFIX}{user_id}"
    profile_details = cache.get(cache_key)
    if profile_details is not None:
        return DotMap(profile_details)
    try:
        user = Person.objects.get(pk=user_id)
    except Person.DoesNotExist:
        user = None
    return user
