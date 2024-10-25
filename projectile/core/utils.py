import hashlib
import os
import json
import logging
import re
import datetime

from datetime import timedelta

import pandas as pd

from django.db import transaction, IntegrityError
from django.db.models import Q, F, Count, Case, When, FloatField, Sum, Max, DateField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from common.enums import Status
from core.enums import SerialType, PersonGroupType
from ecommerce.enums import ShortReturnLogType

from pharmacy.enums import GlobalProductCategory, OrderTrackingStatus
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)

DELIMITER = "5b7886785f"


def get_activation_token(profile):
    """
    Returns a sha256 hexdigest string"
    """
    hashed = hashlib.sha256(str(profile.date_joined)).hexdigest()
    return "{}{}{}".format(profile.pk, DELIMITER, hashed[:40])

# pylint: disable=invalid-name


def extract_pk_from_activation_token(token):
    return token.split(DELIMITER)[0]

# pylint: disable=invalid-name


def getCountryCode(country):
    if country:
        try:
            data = open(os.path.join(REPO_DIR, 'assets/country-code.json'), 'r')
            json_data = json.load(data)
            countryCode = [elem for elem in json_data if elem['label'] == country]
            code = countryCode[0]
        except (IndexError, EOFError, IOError) as exception:
            logger.exception(exception)
            return None
        return code


# pylint: disable=invalid-name


def get_date_format_list():
    try:
        data = open(os.path.join(REPO_DIR, 'assets/date-format.json'), 'r')
        json_item = json.load(data)
    except (IndexError, EOFError, IOError) as exception:
        logger.exception(exception)
    return json_item

# pylint: disable=invalid-name


def getCountryList():
    try:
        data = open(os.path.join(REPO_DIR, 'assets/country-code.json'), 'r')
        json_data = json.load(data)
    except (IndexError, EOFError, IOError) as exception:
        logger.exception(exception)
    return json_data

# pylint: disable=invalid-name

def isDate(string):
    try:
        date_pattern = re.search("(\d{2}[-.]+\d{2}[-.]+\d{4})", string)
        if date_pattern is not None and date_pattern != 'None':
            return True
        else:
            return False
    except ValueError:
        return False


# pylint: disable=invalid-name

def formatDate(date):
    try:
        date_pattern = datetime.datetime.strptime(date, '%d-%m-%Y').strftime('%Y-%m-%d')
        return date_pattern
    except ValueError:
        return False


def parse_int(s):
    try:
        res = int(eval(str(s)))
        if type(res) == int:
            return res
    except:
        return 0


def genarate_patient_code(organization=None, patient=None, increment_value=""):
    """
    [takes current organization then return generated code]

    Returns:
        [string] -- [patient code]
    """
    from core.models import PersonOrganization, OrganizationSetting

    settings = organization.get_settings()
    # organizational patient code setting
    code_prefix = settings.patient_code_prefix
    code_length = settings.patient_code_length
    # calculating length for limiting at most 16 digit
    prefix_length = len(code_prefix)
    length = code_length - prefix_length
    if length <= 0:
        length = 5

    if patient:
        patient = patient.organization_wise_serial
    elif settings.serial_type == SerialType.ORGANIZATION_WISE:
        patient = PersonOrganization.objects.filter(
            organization=organization,
            status__in=[Status.ACTIVE, Status.INACTIVE],
            person_group=PersonGroupType.PATIENT
        ).count() + 1
    else:
        patient = PersonOrganization.objects.filter(
            status__in=[Status.ACTIVE, Status.INACTIVE],
            person_group=PersonGroupType.PATIENT
        ).count() + 1
    if increment_value and isinstance(increment_value, int):
        patient += increment_value

    patient_code = u"{}{:0{length}d}".format(
        code_prefix, patient, length=length)
    return patient_code


def get_global_product_category(organization):
    from .models import OrganizationSetting
    category = OrganizationSetting.objects.values_list(
        'global_product_category', flat=True
    ).get(organization=organization)
    if category == GlobalProductCategory.DEFAULT:
        return [GlobalProductCategory.DEFAULT]
    return [category, GlobalProductCategory.DEFAULT]


def get_person_and_person_organization_common_arguments(obj):
    '''
    common arguments of person and person organization
    '''
    from .models import Person, PersonOrganization
    # Get the field name of the person
    person_fields = [field.name for field in Person._meta.local_fields]
    # Get the field name of the person organization
    person_organization_fields = [
        field.name for field in PersonOrganization._meta.local_fields]
    # Get the common fields of the two models using set
    attributes = set(person_fields) & set(person_organization_fields)
    item_remove = ['id', 'alias']
    attributes = attributes - set(item_remove)
    arguments = {}

    for attribute in attributes:
        attribute_value = getattr(obj, attribute)

        if attribute_value is not None:
            arguments[attribute] = attribute_value

    # Get Country Code From Country Object
    country_code = getCountryCode(obj.country)

    arguments['person'] = obj
    arguments['country_code'] = country_code['code']
    return arguments

def create_prescriber_permission(person_organization):
    """
    Create prescriber permission for a given person organization instance
    """
    from .models import GroupPermission, PersonOrganizationGroupPermission
    # # Find instance of Prescriber Group Permission
    prescriber_permission = GroupPermission.objects.get(name='Prescriber')
    # delete all the previous data
    # PersonOrganizationGroupPermission.objects.filter(
    #     person_organization=person_organization
    # ).delete()
    # create prescriber permission for this prescriber
    permission, created = PersonOrganizationGroupPermission.objects.get_or_create(
        person_organization=person_organization,
        permission=prescriber_permission,
        status=Status.ACTIVE
    )
    if created:
        PersonOrganizationGroupPermission.objects.filter(pk=permission.id).update(
            entry_by=person_organization.entry_by
        )


def create_person_organization_instance(obj):
    """
    Create a person organization instance after saving a person
    """
    arguments = get_person_and_person_organization_common_arguments(obj)

    if arguments['person_group'] in (PersonGroupType.SYSTEM_ADMIN, PersonGroupType.MONITOR):
        from .models import Organization
        organizations = Organization.objects.all()
        # Update organization if its blanks in person instance
        if obj.organization is None:
            obj.organization = organizations[0]
            obj.save(update_fields=['organization'])

        # create person organization for all organizations of a person
        for organization in organizations:
            arguments['organization'] = organization
            create_person_organization(**arguments)
    else:
        create_person_organization(**arguments)

    return True


def create_person_organization(**arguments):
    """
    Create Person Organization Instance
    """
    from .models import PersonOrganization
    try:
        with transaction.atomic():
            person_organization = PersonOrganization.objects.create(**arguments)
            if person_organization.person_group == PersonGroupType.PRESCRIBER:
                # by default set prescriber group permission for newly added prescriber
                create_prescriber_permission(person_organization)
            return person_organization
    except IntegrityError:
        return False


def construct_person_organization_from_dictionary(obj):
    """[get plain object and return like the person organization object]
    Arguments:
        obj {[dict]} -- [description]
    """
    return {
        'id': obj.get('person_organization__id'),
        'alias': obj.get('person_organization__alias'),
        'first_name': obj.get('person_organization__first_name'),
        'last_name': obj.get('person_organization__last_name'),
        'degree': obj.get('person_organization__degree'),
        'phone': obj.get('person_organization__phone'),
        'person_group': obj.get('person_organization__person_group'),
        'designation': {
            'name': obj.get('person_organization__designation__name'),
            'department': {
                'name': obj.get(
                    'person_organization__designation__department__name'),
            }
        }
    }

def construct_organization_object_from_dictionary(obj):
    """[get plain object and return like organization object]
    Arguments:
        obj {[dict]} -- [description]
    """
    return {
        'id': obj.get('organization', None),
        'alias': obj.get('organization__alias', None),
        'name': obj['organization__name'],
        'primary_mobile': obj['organization__primary_mobile'],
        'address': obj['organization__address'],
    }


def get_manager_for_employee(employee_id):
    """
    Get manager for a given employee ID/PK
    """
    from core.models import EmployeeManager

    responsible_employee_manager = EmployeeManager.objects.values_list(
        'manager',
        flat=True
    ).filter(
        employee__id=employee_id,
        status=Status.ACTIVE
    )
    if responsible_employee_manager.exists():
        return responsible_employee_manager.first()
    else:
        return None


def user_detail_cache_expires_by_organization_delivery_thana(thana: list):
    """Expires cache entries for user profiles based on their organization's delivery_thana."""

    from django.core.cache import cache
    from core.models import Person
    from common.cache_keys import USER_PROFILE_DETAILS_CACHE_KEY_PREFIX

    # using set to remove duplicate thana
    thana = list(set(thana))
    user_ids = Person().get_all_actives().filter(
        organization__delivery_thana__in = thana
        ).only("id").values_list("id",flat=True)

    # Create cache keys
    cache_keys = [f"{USER_PROFILE_DETAILS_CACHE_KEY_PREFIX}{user_id}" for user_id in user_ids]

    cache.delete_many(cache_keys)
    logger.info("Expired cache of user detail for their delivery_hub area!")


def generate_unique_otp(length=6) -> str:
    import random

    otp = "".join(random.choices("0123456789", k=length))

    return otp


def update_permissions_for_person(person_organization: int, permission_ids: list[int] = []):
    """While adding permission for a person add the permissions in perosn and person organization model."""
    from core.models import GroupPermission, PersonOrganization, Person

    permissions = (
        GroupPermission()
        .get_all_actives()
        .filter(id__in=permission_ids)
        .values_list("name", flat=True)
        .order_by("name")
    )
    permission_names = ", ".join(permissions)
    # Populate permissions in person organization model
    PersonOrganization.objects.filter(id=person_organization).update(
        permissions=permission_names
    )
    # Populate permissions in person model
    Person.objects.filter(person_organization__id=person_organization).update(
        permissions=permission_names
    )


def get_organization_order_insights(organization_id:int):
    from ecommerce.models import OrderInvoiceGroup
    from common.utils import DistinctSum
    # get the current date
    current_date = timezone.now().date()

    start_date = timezone.datetime(2020, 1, 1).date()

    # Define the boundaries for each group based on date range
    date_ranges = {
        "last_7_days": current_date - timedelta(days=7),
        "last_15_days": current_date - timedelta(days=15),
        "last_30_days": current_date - timedelta(days=30),
        "last_60_days": current_date - timedelta(days=60),
        "last_90_days": current_date - timedelta(days=90),
        "last_120_days": current_date - timedelta(days=120),
        "last_180_days": current_date - timedelta(days=180),
    }
    year_ranges = {}
    # current day to first january of current year
    year_ranges["current_year"] = (timezone.datetime(current_date.year, 1, 1).date(), current_date)

    current_year = current_date.year - 1

    while current_year >= start_date.year:
        start_of_year = timezone.datetime(current_year, 1, 1).date()
        end_of_year = timezone.datetime(current_year, 12, 31).date()
        year_ranges[current_year] = (start_of_year, end_of_year)
        current_year -= 1

    # Query the data and annotate totals for each group
    queryset = OrderInvoiceGroup.objects.filter(
        status__in=[Status.ACTIVE, Status.DRAFT],
        delivery_date__gte=start_date,
        organization_id=organization_id,
    ).exclude(
        current_order_status__in=[
            OrderTrackingStatus.PENDING,
            OrderTrackingStatus.ACCEPTED,
            OrderTrackingStatus.READY_TO_DELIVER,
            OrderTrackingStatus.ON_THE_WAY,
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED,
            OrderTrackingStatus.IN_QUEUE,
        ]
    ).annotate(
        truncated_date=TruncDate("delivery_date", output_field=DateField())
    ).order_by("-id").values("truncated_date").annotate(
        invoice_id = F("id"),
        total_invoice_amount=Coalesce(
            DistinctSum(
                F("sub_total") + F("round_discount") - F("discount") - F("additional_discount"),
                output_field=FloatField(),
            ),
            0.00,
        ),
        total_short=Coalesce(
            Sum(
                Case(
                    When(
                        ~Q(status=Status.INACTIVE)
                        & ~Q(invoice_groups__status=Status.INACTIVE)
                        & Q(invoice_groups__type=ShortReturnLogType.SHORT),
                        then=F("invoice_groups__short_return_amount")
                        + F("invoice_groups__round_discount"),
                    ),
                    output_field=FloatField(),
                )
            ),
            0.00,
        ),
        total_return=Coalesce(
            Sum(
                Case(
                    When(
                        ~Q(status=Status.INACTIVE)
                        & ~Q(invoice_groups__status=Status.INACTIVE)
                        & Q(invoice_groups__type=ShortReturnLogType.RETURN),
                        then=F("invoice_groups__short_return_amount")
                        + F("invoice_groups__round_discount"),
                    ),
                    output_field=FloatField(),
                )
            ),
            0.00,
        ),
        total_short_quantity=Coalesce(
            Sum(
                Case(
                    When(
                        ~Q(status=Status.INACTIVE)
                        & ~Q(invoice_groups__status=Status.INACTIVE)
                        & Q(invoice_groups__type=ShortReturnLogType.SHORT),
                        then=F("invoice_groups__total_short_return_items")
                    ),
                    output_field=FloatField(),
                )
            ),
            0.00,
        ),
        total_return_quantity=Coalesce(
            Sum(
                Case(
                    When(
                        ~Q(status=Status.INACTIVE)
                        & ~Q(invoice_groups__status=Status.INACTIVE)
                        & Q(invoice_groups__type=ShortReturnLogType.RETURN),
                        then=F("invoice_groups__total_short_return_items")
                    ),
                    output_field=FloatField(),
                )
            ),
            0.00,
        ),
        unique_item=Count(
            Case(
                When(
                    orders__stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                    then=F("orders__stock_io_logs__stock"),
                )
            ),
            distinct=True,
        ),
        total_item=Coalesce(
            Sum(
                Case(
                    When(
                        orders__stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                        then=F("orders__stock_io_logs__quantity"),
                    )
                )
            ),
            0.00,
        ),
    )
    # create dataframe from queryset data
    df = pd.DataFrame(queryset)
    # if dataframe is empty then return detail message.
    if df.empty:
        return {"detail": "No order available for the organization."}

    # Declare a list to store order summary based on date ranges
    order_summary = []
    last_order_summary = df.iloc[0]

    last_order_summary_obj = {
        "date_range": "last_order",
        "number_of_invoices": 1,
        "total_order_amount": round(last_order_summary["total_invoice_amount"], 2),
        "total_short_amount": round(last_order_summary["total_short"], 2),
        "total_return_amount": round(last_order_summary["total_return"], 2),
        "total_short_quantity": round(last_order_summary["total_short_quantity"], 2),
        "total_return_quantity": round(last_order_summary["total_return_quantity"], 2),
        "unique_item": last_order_summary["unique_item"],
        "total_item": last_order_summary["total_item"]
    }
    # Append last_order_summary object
    order_summary.append(last_order_summary_obj)
    # Itereate through order summary based on date ranges
    for key, value in date_ranges.items():
        filtered_data = df[df["truncated_date"].between(value, current_date)]

        totals = {
            "date_range": key,
            "number_of_invoices": filtered_data["invoice_id"].count(),
            "total_order_amount": round(filtered_data["total_invoice_amount"].sum(), 2),
            "total_short_amount": round(filtered_data["total_short"].sum(), 2),
            "total_return_amount": round(filtered_data["total_return"].sum(), 2),
            "total_short_quantity": round(filtered_data["total_short_quantity"].sum(), 2),
            "total_return_quantity": round(filtered_data["total_return_quantity"].sum(), 2),
            "unique_item": filtered_data["unique_item"].sum(),
            "total_item": filtered_data["total_item"].sum()
        }

        order_summary.append(totals)
    # Iterate through year ranges and get the summary.
    for key, value in year_ranges.items():
        filtered_data = df[df["truncated_date"].between(value[0], value[1])]
        totals = {
            "date_range": key,
            "number_of_invoices": filtered_data["invoice_id"].count(),
            "total_order_amount": round(filtered_data["total_invoice_amount"].sum(), 2),
            "total_short_amount": round(filtered_data["total_short"].sum(), 2),
            "total_return_amount": round(filtered_data["total_return"].sum(), 2),
            "total_short_quantity": round(filtered_data["total_short_quantity"].sum(), 2),
            "total_return_quantity": round(filtered_data["total_return_quantity"].sum(), 2),
            "unique_item": filtered_data["unique_item"].sum(),
            "total_item": filtered_data["total_item"].sum()
        }

        order_summary.append(totals)

    return order_summary
