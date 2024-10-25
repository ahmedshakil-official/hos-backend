# - *- coding: utf- 8 - *-
# for python3 compatibility
from __future__ import division

import logging
import pytz
from future.builtins import round
from distutils import util

import mimetypes
import inspect
import re
import json
import math
import os


from calendar import monthrange
from datetime import datetime, date, timedelta, time
from io import BytesIO
from uuid import UUID
from isoweek import Week
from PIL import Image
from validator_collection import checkers
from versatileimagefield.utils import (
    validate_versatileimagefield_sizekey_list,
    get_resized_path
)
from django.conf import settings

from django.core.cache import cache
from django.db.models import Q, Func, Sum
from django.db.utils import IntegrityError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
# rename Q as esQ for same name
from elasticsearch_dsl import Q as esQ

from rest_framework.serializers import (
    ValidationError
)

from common.validators import validate_unique_with_organization
from common.enums import Status, PublishStatus, DiscardType
from core.enums import SerialType
from core.utils import getCountryCode
from clinic.enums import DaysChoice
from pharmacy.enums import SalesInactiveType


logger = logging.getLogger(__name__)

class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s::numeric, 3)"

class ArrayLength(Func):
    function = 'CARDINALITY'

class DistinctSum(Sum):
    function = "SUM"
    template = "%(function)s(DISTINCT %(expressions)s)"

DAYS_OF_WEEK = ('Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')

def validate_week(week):
    if int(week) in range(1, 52 + 1):
        week = int(week)
    else:
        raise ValueError(
            "Invalid week ({}). Must be between 1 and 52.".format(week))

    return week


def validate_month(month):
    if int(month) in range(1, 12 + 1):
        month = int(month)
    else:
        raise ValueError(
            "Invalid month ({}). Must be between 1 and 12.".format(month))

    return month


def validate_year(year):
    now = datetime.now()
    if int(year) in range(1900, now.year + 1):
        year = int(year)
    else:
        raise ValueError(
            "Invalid year ({}). Must be between 1900 and {}.".format(year, now.year))

    return year


def days_in_month(year, month):
    year = validate_year(year)
    month = validate_month(month)
    return monthrange(year, month)[1]


def get_day_code(name):
    attributes = inspect.getmembers(
        DaysChoice,
        lambda a: not inspect.isroutine(a))
    choices = [day for day in attributes if \
              not(day[0].startswith('__') and day[0].endswith('__'))]
    code = [item[1] for item in choices if name in item]
    return code[0]


def daterange(start_date, end_date):
    if not start_date and not end_date:
        return None
    if not start_date:
        start_date = datetime.today().strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.today().strftime("%Y-%m-%d")

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    dates = []
    for date in range(int((end_date - start_date).days) + 1):
        dates.append((start_date + timedelta(date)).strftime("%Y-%m-%d"))
    return dates


def days_generator(start_date, end_date):
    if not start_date and not end_date:
        return None
    if not start_date:
        start_date = datetime.today().strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.today().strftime("%Y-%m-%d")

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    days_generator = (start_date + timedelta(x) \
                      for x in range((end_date - start_date).days + 1))
    return days_generator


def get_days_from_date_range(start_date, end_date):
    days = []
    try:
        for day in days_generator(start_date, end_date):
            days.append(get_day_code(day.strftime("%A").upper()))
        return days
    except TypeError:
        return days


def get_day_from_date(date_obj=None):
    if not date_obj:
        date_obj = datetime.today().strftime("%Y-%m-%d")
    date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
    return str(get_day_code(date_obj.strftime("%A").upper()))


def get_date_obj_from_date_str(date_str, _format):
    if date_str:
        date_obj = datetime.strptime(date_str, _format).date()
        return date_obj

# pylint: disable=invalid-name
def get_datetime_obj_from_datetime_str(datetime_str, _format="%Y-%m-%d %H:%M:%S", time_format=""):
    """
    get a datetime or date string and convert it to datetime object

    Arguments:
        datetime_str {string} -- date or datetime string
        _format {string} -- datetime format string
        time_format {string} -- time format string of a date

    Returns:
        {object} -- datetime object
    """
    if datetime_str:
        try:
            datetime_obj = timezone.make_aware(
                datetime.strptime(datetime_str, _format),
                timezone.get_current_timezone()
            )
        except ValueError:
            time_format = time_format if time_format else "%H:%M:%S"
            datetime_str = u"{} {}".format(
                datetime_str,
                datetime.now().strftime(time_format)
            )
            datetime_obj = timezone.make_aware(
                datetime.strptime(datetime_str, _format),
                timezone.get_current_timezone()
            )
        return datetime_obj


def get_datetime_obj_from_date_str(date_str, _format):
    """[summary]
    Take a date string and return datetime with current time
    Arguments:
        date_str {[string]} -- [date string(2018-12-12)]
        _format {[string]} -- [desire output format for datetime object]

    Returns:
        [object] -- [datetime object combining current time with passing date str]
    """
    if date_str:
        datetime_str = u"{}{}{}".format(
            date_str, "T", datetime.now().strftime("%H:%M:%S"))
        datetime_obj = timezone.make_aware(
            datetime.strptime(datetime_str, _format),
            timezone.get_current_timezone()
        )
        return datetime_obj

def get_date_from_day_code(day):
    today = date.today()
    for i in range(7):
        _date = today - timedelta(i)
        weekday = int(_date.weekday())
        if weekday == day:
            return _date
    return today

def get_week_dates_range_before_or_till_today(date_str=None):
    """[return date ranges from Saturday to Today]
    Returns:
        [list] -- [description]
    """
    if date_str:
        today = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        today = datetime.now()
    today_name = today.strftime("%A")
    today_in_week_list = DAYS_OF_WEEK.index(today_name)
    end_date = today.strftime("%Y-%m-%d")
    for day in range(today_in_week_list + 1):
        start_date = today - timedelta(day)
        start_date = start_date.strftime("%Y-%m-%d")
    return [start_date, end_date]

def get_patient_schedule_str(appointment):
    """[summary]
    Take schedule instance and return final schedule string
    Arguments:
        appointment {[model instance]} -- [instance of appointmnet schedule]

    Returns:
        [str] -- [String of patient schedule(Sun, Mon etc.)]
    """
    days = []
    day_choise = DaysChoice.get_dict()
    schedules = appointment.person.patient_appointment_schedules.filter(
        status=Status.ACTIVE,
        organization=appointment.organization
    )
    for item in schedules:
        days.append(
            list(day_choise.keys())[list(day_choise.values()).index(item.days)].capitalize()[:3]
        )
    days = set(days)
    if len(days) > 0:
        days_str = u"{}".format(', '.join(days))
    else:
        return None
    return days_str.strip()


def get_weekly_range(year, week):
    """
    Returns tuple of first and last date of
    """
    week = Week(year, week)
    return week.monday(), week.sunday()


def get_monthly_range(year, month):
    """
    Returns tuple with first and last date of given month
    """
    days = days_in_month(year, month)
    return date(year, month, 1), date(year, month, days)


def get_yearly_range(year):
    """
    Returns tuple with first and last date of given year
    """
    return date(year, 1, 1), date(year, 12, 31)


def get_week(_date=None):
    """
    Return current week of today or of the date given
    """
    if _date is None:
        _date = date.today()
    return _date.isocalendar()[1]

def flip_horizontal(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)

def flip_vertical(im):
    return im.transpose(Image.FLIP_TOP_BOTTOM)

def rotate_180(im):
    return im.transpose(Image.ROTATE_180)

def rotate_90(im):
    return im.transpose(Image.ROTATE_90)

def rotate_270(im):
    return im.transpose(Image.ROTATE_270)

def transpose(im):
    return rotate_90(flip_horizontal(im))

def transverse(im):
    return rotate_90(flip_vertical(im))

orientation_funcs = [None,
                     lambda x: x,
                     flip_horizontal,
                     rotate_180,
                     flip_vertical,
                     transpose,
                     rotate_270,
                     transverse,
                     rotate_90
                    ]

def apply_image_orientation(image):
    """
    Extract the oritentation EXIF tag from the image, which should be a PIL Image instance,
    and if there is an orientation tag that would rotate the image, apply that rotation to
    the Image instance given to do an in-place rotation.

    :param Image im: Image instance to inspect
    :return: A possibly transposed image instance
    """

    try:
        kOrientationEXIFTag = 0x0112
        if hasattr(image, '_getexif'): # only present in JPEGs
            event = image._getexif()       # returns None if no EXIF data
            if event is not None:
                orientation = event[kOrientationEXIFTag]
                func = orientation_funcs[orientation]
                return func(image)
    except:
        return image
    return image


def clean_image(image):
    output = BytesIO()
    actual_image = Image.open(image)
    oriented_image = apply_image_orientation(actual_image)
    data = list(oriented_image.getdata())
    image_without_exif = Image.new(oriented_image.mode, oriented_image.size)
    image_without_exif.putdata(data)
    image_without_exif.save(output, format='JPEG')
    output.seek(0)
    #change the imagefield value to be the newley modifed image value
    return InMemoryUploadedFile(output, None, ".jpg", 'image/jpeg', None, None)


def get_person_phone_no(paid_by):

    country_code = getCountryCode(paid_by.country)['code']
    phone_no = paid_by.phone
    if phone_no[0] == '0':
        phone_no = '{}{}'.format(phone_no[:0], phone_no[1:])
    return '{}{}'.format(country_code, phone_no)


def prepare_start_date(date, time_=time.min):
    '''
    Prepare date by adding timezone for minimun
    '''
    date = datetime.combine(
        datetime.strptime(date, '%Y-%m-%d'), time_)

    date = timezone.make_aware(
        date, timezone.get_current_timezone())
    return date


def prepare_datetime_by_timestamp(timestamp):
    """
    Prepare datetime by timestamp using timezone
    """
    date_time = datetime.fromtimestamp(timestamp)
    date_time = timezone.make_aware(
        date_time, timezone.get_current_timezone()
    )
    return date_time


def prepare_end_date(date, time_=time.max):
    '''
    Prepare date by adding timezone for maximum
    '''
    date = datetime.combine(
        datetime.strptime(date, '%Y-%m-%d'), time_)

    date = timezone.make_aware(
        date, timezone.get_current_timezone())
    return date


def expire_cache(cache_key_pattern):
    cache.delete_pattern(cache_key_pattern, itersize=10000)


def get_ratio(whole_number, sliced_number):
    if whole_number != 0:
        return (sliced_number/whole_number)*100
    return 0

def get_timezone_aware_current_time():
    '''
    make timezone aware time from datetime.datetime.now()
    '''
    return timezone.make_aware(datetime.now(), timezone.get_current_timezone())

def prepare_date_range_filter_arguments(self, field_name):
    '''
    Prepare filter queryset arguments with date range
    '''
    start_date = self.request.query_params.get('date_0', None)
    end_date = self.request.query_params.get('date_1', None)

    start_date = prepare_start_date(start_date)
    end_date = prepare_end_date(end_date)

    values = {
        'organization':  self.request.user.organization,
        'status': Status.ACTIVE,
        '{0}__range'.format(field_name): [start_date, end_date]
    }
    arguments = {}
    for key, value in values.items():
        if value is not None:
            arguments[key] = value
    return arguments


def create_cache_key_name(self, model_name, cache_name=None):
    organization = ""
    if hasattr(self, 'request'):
        organization = str(format(self.request.user.organization_id, '04d'))
    else:
        if self.organization:
            organization = str(format(self.organization.id, '04d'))
        else:
            organization = 'global'
    if cache_name:
        # generate key to set and get cache
        key_name = '{}_{}_omis_{}'.format(organization, model_name, cache_name)
    else:
        # generate key to delete matching cache pattern
        key_name = '{}_{}_omis_*'.format(organization, model_name)
    return key_name


def get_global_based_discarded_list(self, model=None, organization=None):
    """[takes view class or model, then determine the model class and
    return list if global and used as clone to other]

    Returns:
        [list] -- [list of primary key]
    """

    if model:
        model_class = model
    else:
        model_class = self.get_serializer_class().Meta.model

    if organization:
        _organization = organization
    else:
        _organization = self.request.user.organization_id


    discarded_lists = model_class.objects.values_list(
        'clone__pk', flat=True
    ).filter(
        status=Status.ACTIVE,
        organization=_organization,
        is_global=PublishStatus.PRIVATE,
        clone__is_global__in=[
            PublishStatus.INITIALLY_GLOBAL,
            PublishStatus.WAS_PRIVATE_NOW_GLOBAL]
    )
    return list(set(discarded_lists))


def get_global_or_organization_wise_active_list(self, model):
    return model.objects.filter(
        Q(organization=self.request.user.organization) \
        | Q(is_global=PublishStatus.INITIALLY_GLOBAL) \
        | Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
        status=Status.ACTIVE,
    )


def get_organization_wise_serial(self):
    """
    [takes model class and
    return organization and status wise serial
    if organization is available, otherwise only status wise serial]

    Returns:
        [integer] -- [organization or status wise serial]
    """

    if hasattr(self, 'organization'):
        serial_data = self.__class__.objects.filter(
            organization=self.organization,
            status__in=[self.status, Status.INACTIVE]
        )
        if hasattr(self, 'person_group'):
            serial_data = serial_data.filter(
                person_group=self.person_group,
            )
    else:
        serial_data = self.__class__.objects.filter(
            status__in=[self.status, Status.INACTIVE]
        )
    # categorize sales serial for different types of sales
    if self.__class__.__name__ == 'Sales':
        exclude_types = [SalesInactiveType.FROM_EDIT]
        if self.status == Status.ACTIVE:
            exclude_types.append(SalesInactiveType.FROM_ON_HOLD)
            serial_data = serial_data.exclude(
                inactive_from__in=exclude_types
            )
        elif self.status == Status.ON_HOLD:
            exclude_types.append(SalesInactiveType.FROM_ACTIVE)
            serial_data = serial_data.exclude(
                inactive_from__in=exclude_types
            )
    return serial_data.count() + 1


def filter_global_product_based_on_settings(self, queryset=None, key=None):
    """
    takes queryset and key
    key used to check is it call from search endpoint or not
    return queryset based on show global product in organization settings
    Returns: this method returns queryset
    """
    # check global products true or false
    show_global_product = self.request.user.profile_details.organization.show_global_product

    # if key is none then filter data for product endpoint
    if queryset is not None and key is None:
        # if show global product false then filter only private product
        if not show_global_product:
            if queryset.count() > 0 and hasattr(queryset[0], 'is_global'):
                queryset = queryset.filter(is_global=PublishStatus.PRIVATE)
            else:
                queryset = queryset.filter(
                    product__is_global=PublishStatus.PRIVATE)

    # if key is search then filter data for search endpoint
    elif queryset is not None and key == 'search':
        if show_global_product:
            query = \
                esQ(
                    "match", is_global=PublishStatus.INITIALLY_GLOBAL
                ) | esQ(
                    "match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL
                ) | esQ(
                    "match", organization__pk=self.request.user.organization_id
                )
        else:
            query = \
                esQ(
                    "match", is_global=PublishStatus.PRIVATE
                ) & esQ(
                    "match", organization__pk=self.request.user.organization_id
                )
        queryset = queryset.filter(query)
    return queryset


def generate_code_with_hex_of_organization_id(request, code=''):
    if isinstance(request, int):
        org_id = request
    else:
        org_id = request.user.organization_id
    # create 6 length hexadecimal value with organization id
    return hex(org_id)[2:].zfill(6) + code

def get_product_code_or_none_from_dict(organization, data, key):
    from pharmacy.models import Product
    try:
        if data[key]:
            code = str(data[key])
            if len(code) >= 5 and len(code) <= 15:
                value = generate_code_with_hex_of_organization_id(
                    organization, code
                )
                if not validate_unique_with_organization(organization, value, 'code', Product):
                    raise IntegrityError('code: {}. Duplicate code.'.format(code))
                return value
            raise IntegrityError('code: {}, Code length should be 5 to 15.'.format(code))
        return None
    except (ValueError, KeyError):
        return None


def isclose(value_1, value_2, rel_tol=1e-09, abs_tol=0.0):
    """
    Get two number and return true if equal otherwise return false
    """
    value_1 = round(float(str(value_1)), 3)
    value_2 = round(float(str(value_2)), 3)
    return abs(value_1 - value_2) <= max(rel_tol * max(abs(value_1), abs(value_2)), abs_tol)


def re_validate_grand_total(grand_total, calculated_grand_total):
    """[summary]
    Arguments:
        grand_total {[float]} -- [description]
        calculated_grand_total {[float]} -- [description]
    Raises:
        ValidationError: [return validation error if two float value not close]
    """
    if not isclose(grand_total, calculated_grand_total, rel_tol=0.001):
        raise ValidationError({
            'error': 'INVALID_PURCHASE_DUE_TO_INCORRECT_GRAND_TOTAL',
        })


def create_bulk_transaction(self, data, custom_info, sales_id=None, organization=None, entry_by=None):
    """
    Take transaction object and create bulk transaction
    """
    from account.models import Transaction
    from account.enums import TransactionFor
    from account.serializers import TransactionPurchaseSerializer
    transactionItems = []

    if organization is None:
        _organization = self.request.user.organization
    else:
        _organization = organization

    if entry_by is None:
        _entry_by = self.request.user
    else:
        _entry_by = entry_by

    for item in data:
        if custom_info and 'paid_by' in custom_info:
            item['paid_by'] = custom_info['paid_by']
            item['person_organization'] = custom_info['person_organization']
            item['code'] = custom_info['code']
        transaction = Transaction(
            paid_by_id=item['paid_by'],
            person_organization_id=item['person_organization'],
            received_by_id=item['received_by'],
            person_organization_received_id=item['person_organization_received'],
            organization=_organization,
            date=get_datetime_obj_from_datetime_str(
                item['date'], '%Y-%m-%dT%H:%M:%S'),
            accounts_id=item['accounts'],
            amount=(float(item['amount'])),
            paid_in_note=float(item['paid_in_note']),
            code=item['code'],
            entry_by=_entry_by,
            method=item['method'],
            # sales_id=sales_id,
            head_id=item['head'],
            transaction_for=item['transaction_for'],
            previous_paid=item.get('previous_paid', 0),
            previous_due=item.get('previous_due', 0),
            current_due=item.get('current_due', 0),
        )
        if item['transaction_for'] == TransactionFor.SALE:
            transaction.sales_id = sales_id
        transaction.save()
        if item['transaction_for'] == TransactionFor.PURCHASE:
            transactionItems.append(transaction)

    # create transaction purchase for sales return transaction
    if transactionItems:
        data_list = []
        for item in transactionItems:
            data_list.append({
                'transaction': item.id,
                'purchase': sales_id,
                'amount': item.amount,
                'organization': _organization.pk
            })

        serializer = TransactionPurchaseSerializer(data=data_list, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save(entry_by=_entry_by,)


def create_organization_wise_discarded_item(user, model, item, field_name, _type=DiscardType.EDIT):
    """[Crete organizationwise discarded item containing instance]
    Arguments:
        user {[object]} -- [request.user]
        model {[Model]} -- [target model. eg: OrganizationWiseDiscardedTransactionHead]
        item {[instance]} -- [eg: TransactionHead instance to be add to target model model]
        field_name {[str]} -- [field_name of target model]
    Keyword Arguments:
        _type {Int} -- [common.enums.DiscardType] (default: 1)
    """
    values = {
        '{}'.format(field_name): item,
        'entry_type': _type
    }
    discarded_item = model.objects.create(
        organization=user.organization,
        entry_by=user,
        **values
    )
    discarded_item.save()


def create_discarded_item(model, user, **created_data):
    """[Crete organizationwise discarded item containing instance]
    Arguments:
        user {[object]} -- [request.user]
        model {[Model]} -- [target model. eg: OrganizationWiseDiscardedTransactionHead]
    Keyword Arguments:
        created_data -- [field name of targeted model and its desire value.
            eg: {'product': 10(id or product instance), 'parent': 2(id or product instance), entry_type: DiscardType.MERGE }]
    """
    discarded_item = model.objects.create(
        organization=user.organization,
        entry_by=user,
        **created_data
    )
    discarded_item.save()

def validate_uuid4(uuid_string):
    """
    Validate that a UUID string is in
    fact a valid uuid4.
    Happily, the uuid module does the actual
    checking for us.
    It is vital that the 'version' kwarg be passed
    to the UUID() call, otherwise any 32-character
    hex string is considered valid.
    """
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False
    # If the uuid_string is a valid hex code,
    # but an invalid uuid4,
    # the UUID.__init__ will convert it to a
    # valid uuid4. This is bad for validation purposes.
    return str(val) == str(uuid_string)

def not_blank(restrict_alias=True):
    def wrapper(string):
        if string not in ['', u'', None]:
            if restrict_alias:
                # check whether the alias is corret uuid format
                return validate_uuid4(str(string))
            return True
        return False
    return wrapper

def check_both_global(base, parent):
    """
    base: keeping item
    parent: deleted item
    takes keeping item and deleted item instance
    check is both items are global
    then return true or false
    """
    if base.is_global != PublishStatus.PRIVATE and \
            parent.is_global != PublishStatus.PRIVATE:
        return True
    return False


def sync_queryset(self, queryset):
    min_date = self.request.query_params.get('min_date', None)
    offset = self.request.query_params.get('offset', None)
    sync_state = self.request.query_params.get('sync_state', None)

    if not sync_state:
        return queryset

    if sync_state == "update" and min_date:
        min_date = prepare_datetime_by_timestamp(int(min_date) / 1000)
        queryset = queryset.filter(
            Q(created_at__gt=min_date) | Q(updated_at__gt=min_date)
        )
    if offset:
        queryset = queryset.filter(
            id__gt=offset
        )

    return queryset.order_by("id")


# converter bangla digit to english digit
def convert_bangla_digit_to_english_digit(original=""):
    """
    english_number: It contains list of english digit,
    bangla_number: It contains list of bangla digit,
    original: takes digit input from user,
    character: item,
    After decoding bangla digit then encoding character to match bangla digit,
    then replaced with english number or digit
    then return the converted value.
    """
    converted = ""
    english_number = [
        '0', '1', '2', '3', '4',
        '5', '6', '7', '8', '9'
    ]
    bangla_number = [
        '০', '১', '২', '৩', '৪',
        '৫', '৬', '৭', '৮', '৯'
    ]
    original = original if original else ""

    for character in original:
        character = character
        if character in bangla_number:
            converted += english_number[bangla_number.index(character)]
        else:
            converted += character
    return converted


def mime_content_type(filename):
    """Get mime type
    :param filename: str
    :type filename: str
    :rtype: str
    """
    type_ = mimetypes.MimeTypes().guess_type(filename)[0]
    return type_ if type_ else 'file'


def get_id_fields_based_on_setting(organization, basic_fields, serial_fields):
    """[summary]
    Arguments:
        organization {[model object]} -- [organization instance]
        basic_fields {[list]} -- [id fields]
        serial_fields {[list]} -- [organization_wise_serial related fields]
    """
    return serial_fields if \
        organization.get_settings().serial_type == SerialType.ORGANIZATION_WISE \
        else basic_fields

def inactive_instance(instance):
    """[inactive an model instance/row]
    Arguments:
        instance {[object]} -- [model instance]
    """
    instance.status = Status.INACTIVE
    instance.save()


def string_to_bool(value='False'):
    """[summary]

    Keyword Arguments:
        value {str} -- [string need to be bool] (default: {'False'})

    Returns:
        [boolean] -- [boolean value against string input]
    """
    try:
        return bool(util.strtobool(value))
    except:
        return False


# Parses depth, encoded names into a JSON'ish dictionary structure
def parse_to_dict_val(key, value, dict={}):
    patt = re.compile(r'(?P<name>.*?)[\[](?P<key>.*?)[\]](?P<remaining>.*?)$')
    matcher = patt.match(key)
    tmp = (matcher.groupdict() if not matcher ==
           None else {"name": key, "remaining": ''})
    if tmp['remaining'] == '':
        try:
            dict[tmp['key']] = value
        except:
            pass
    return dict

# Parses dictionary for encoded keys signifying depth
def parse_to_dict_vals(dictin):
    dictout = {}
    for key, value in dictin.items():
        parse_to_dict_val(key, value, dictout)
    return dictout


def generate_map_url_and_address_from_geo_data(header=None):
    if not header:
        return {}
    geo_data = header.get("Geodata", "")
    if not geo_data or geo_data == "null" or geo_data == "undefined":
        return {}
    if geo_data and isinstance(geo_data, str):
        json_acceptable_string = geo_data.replace("'", "\"")
        geo_data = json.loads(json_acceptable_string)
    reverse_geo_code = geo_data.get("reverseGeoCode", {})
    current_position = geo_data.get("currentPosition", {})
    base_map_url = "http://maps.google.com/maps?q="
    address_list = [
        reverse_geo_code.get("name", ""),
        reverse_geo_code.get("street", ""),
        reverse_geo_code.get("district", ""),
        reverse_geo_code.get("region", ""),
    ]
    address_list = list(filter(None, address_list))
    address = ', '.join(address_list)
    map_url = "{}{},{}".format(
        base_map_url,
        current_position.get("latitude", ""),
        current_position.get("longitude", "")
    )
    return {
        "address": address,
        "map_url": map_url
    }

def get_item_from_list_of_dict(_list, key, value):
    item = next(
        filter(
            lambda item: item[key] == value, _list
        ), {}
    )
    return item


def get_item_from_list_of_dict_v2(_list, key1, value1, key2, value2):
    """
    This will take supplier and contractor as key and supplier and contractor id
    as value then it will return the item if contractor and suplier id is matched
    """
    item = next(
        filter(
            lambda item: item[key1] == value1 and item[key2]==value2, _list
        ), {}
    )
    return item

def get_value_or_zero(value=0):
    if not math.isnan(value):
        return value
    return 0


def convert_utc_to_local(dt_utc, local_tz_name='Asia/Dhaka'):
    utc_tz = pytz.timezone('UTC')
    local_tz = pytz.timezone(local_tz_name)
    dt_local = dt_utc.astimezone(local_tz)
    return dt_local


def remove_brackets_from_word(word):
    # Define a string of brackets to remove
    brackets = '()' + '{}' + '[]'

    # Create a translation table that maps each bracket to None
    translator = str.maketrans('', '', brackets)

    # Use the translation table to remove the brackets from the word
    cleaned_word = word.translate(translator)

    return cleaned_word

def get_healthos_settings():
    from common.cache_keys import ORGANIZATION_SETTINGS_CACHE_KEY_PREFIX
    from core.models import Organization

    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)

    org_setting_cache_key = f"{ORGANIZATION_SETTINGS_CACHE_KEY_PREFIX}{distributor_id}"
    org_setting_cache = cache.get(org_setting_cache_key)
    if org_setting_cache:
        setting = org_setting_cache
    else:
        setting = Organization.objects.only('pk').get(pk=distributor_id).get_settings()
    return setting

def get_url_from_image_key(image_path, image_key):
    """Build a URL from `image_key`."""
    img_key_split = image_key.split('__')
    if 'x' in img_key_split[-1]:
        size_key = img_key_split.pop(-1)
    else:
        size_key = ''
    image_size_split = size_key.split('x')
    if len(image_size_split) == 2:
        img_width = image_size_split[0]
        img_height = image_size_split[1]
        img_url = get_resized_path(
            image_path,
            int(img_width),
            int(img_height),
            img_key_split[0],
            ''
        )
    else:
        img_url = image_path
    is_valid_url = checkers.is_url(img_url)
    if is_valid_url:
        return img_url
    return f"{settings.FULL_MEDIA_URL}{img_url}"

def build_versatileimagefield_url_set_from_image_name(image_name, size_set, request=None):
    """
    Return a dictionary of urls corresponding to size_set
    - `image_name`: name of an image from image field
    - `size_set`: An iterable of 2-tuples, both strings. Example:
        [
            ('large', 'url'),
            ('medium', 'crop__400x400'),
            ('small', 'thumbnail__100x100')
        ]

        The above would lead to the following response:
        {
            'large': 'http://some.url/image.jpg',
            'medium': 'http://some.url/__sized__/image-crop-400x400.jpg',
            'small': 'http://some.url/__sized__/image-thumbnail-100x100.jpg',
        }
    - `request`:
    """
    size_set = validate_versatileimagefield_sizekey_list(size_set)
    to_return = {}
    if image_name:
        for key, image_key in size_set:
            img_url = get_url_from_image_key(image_name, image_key)
            if request is not None:
                img_url = request.build_absolute_uri(img_url)
            to_return[key] = img_url
    return to_return


def get_permission_cache_key(person_id, organization_id, group_name):
    """
    Generate a cache key for permission lookup based on person ID, organization ID, and group name.

    Args:
    - person_id (int): The ID of the person.
    - organization_id (int or None): The ID of the organization. If None, defaults to 0.
    - group_name (str): The name of the group.

    Returns:
    - str: A cache key formatted as "permission_{person_id}_{organization_id}_{group_name}".
    """
    # Check if organization_id is None and set it to 0 if so
    if organization_id is None:
        organization_id = 0
    else:
        organization_id = organization_id

    # Generate the cache key with formatted strings
    cache_key = "permission_{}_{}_{}".format(
        str(person_id).zfill(7),
        str(organization_id).zfill(7),
        group_name
    )
    return cache_key

def track_execute_time(print_time=True):
    import time

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            if print_time:
                logger.info(
                    f"`{func.__name__}` took `{execution_time:.2f}` seconds to complete."
                )

            return result

        return wrapper

    return decorator
