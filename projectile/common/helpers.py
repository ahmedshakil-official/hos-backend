# -*- coding: utf-8 -*-

import datetime as DT
import json
import csv
import codecs
import logging
import os
import sys
import random
import time as tm
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from slugify import slugify
import dotenv

from common.enums import PublishStatus, Status
from common.utils import prepare_start_date, prepare_end_date
from core.enums import AllowOrderFrom

logger = logging.getLogger(__name__)

# pylint: disable=old-style-class, no-init
class ReleaseTagManager:

    cache_key = 'RELEASE_TAG'
    time_format = "%Y%m%d-%H%M%S"

    @staticmethod
    def set():
        now = datetime.now().strftime(ReleaseTagManager.time_format)
        cache.set(ReleaseTagManager.cache_key, now, 0)
        logger.info("Release tag was set to: {}".format(now))

    @staticmethod
    def get():
        cached = cache.get(ReleaseTagManager.cache_key)
        if cached:
            return cached
        now = datetime.now().strftime(ReleaseTagManager.time_format)
        return now

def prepare_es_populate_filter(filters={'status' : Status.ACTIVE}):
    start_date = os.environ.get('ES_FILTER_START_DATE', None)
    end_date = os.environ.get('ES_FILTER_END_DATE', None)

    if end_date and start_date:
        start_date_time = prepare_start_date(start_date)
        end_date_time = prepare_end_date(end_date)

        filters['created_at__range'] = [start_date_time, end_date_time]

    return filters


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
            "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                            "(or 'y' or 'n').\n")

def get_release_tag():
    if settings.DEBUG:
        return str(int(tm.time()))
    return ReleaseTagManager.get()


def get_secret_key():
    string_ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    # pylint: disable=unused-variable
    key_ = ''.join([random.SystemRandom().choice(string_) for i in range(50)])
    return key_


def get_date_from_period(period):
    date_to_return = date.today()
    if period == '1w':
        date_to_return = date.today() + relativedelta(days=-7)
    elif period == '1m':
        date_to_return = date.today() + relativedelta(months=-1)
    elif period == '3m':
        date_to_return = date.today() + relativedelta(months=-3)
    elif period == '6m':
        date_to_return = date.today() + relativedelta(months=-6)
    elif period == 'ty':
        date_to_return = date(date.today().year, 1, 1)
    elif period == '1y':
        date_to_return = date.today() + relativedelta(years=-1)
    elif period == '3y':
        date_to_return = date.today() + relativedelta(years=-3)
    elif period == '5y':
        date_to_return = date.today() + relativedelta(years=-5)
    else:
        date_to_return = date.today()

    return date_to_return


def get_date_time_from_period(period):
    current_time_now = timezone.now()
    today_start_time = datetime.combine(current_time_now.date(), datetime.min.time())

    if period == '1w':
        date_time_to_return = today_start_time - timedelta(days=7)
    elif period == '1m':
        date_time_to_return = today_start_time - timedelta(days=30)
    else:
        date_time_to_return = today_start_time

    return date_time_to_return


def get_all_date_from_period():
    keys = {'td', '1w', '1m', '3m', '6m', 'ty', '1y', '3y', '5y'}
    _date = {}
    for key in keys:
        _date[k] = get_date_from_period(key)
    return _date


def get_date_range_from_period(period, _date_time=False, _dict=True):
    from common.utils import prepare_start_date, prepare_end_date
    # LM = Last Month
    # TM = This Month
    period_list = ['LM', 'lm', 'TM', 'tm']
    if not period in period_list:
        raise ValueError(f"Invalid period: {period}, Please use any from {period_list}")

    if period in ['LM', 'lm']:
        end_date = date.today().replace(day=1) - timedelta(days=1)
        start_date = date.today().replace(day=1) - timedelta(days=end_date.day)
    elif period in ['TM', 'tm']:
        start_date = date.today().replace(day=1)
        end_date = date.today()

    if _date_time:
        start_date = prepare_start_date(str(start_date))
        end_date = prepare_end_date(str(end_date))
    if _dict:
        return {
            'start_date': start_date,
            'end_date': end_date
        }
    return start_date, end_date


def prepare_start_date_end_date(period):
    start_date = str(get_date_from_period(period))
    start_date = datetime.combine(
        datetime.strptime(start_date, '%Y-%m-%d'), time.min)
    end_date = str(date.today())
    end_date = datetime.combine(
        datetime.strptime(end_date, '%Y-%m-%d'), time.max)
    start_date = timezone.make_aware(
        start_date, timezone.get_current_timezone())
    end_date = timezone.make_aware(
        end_date, timezone.get_current_timezone())
    return start_date, end_date

def get_global_active_record(model_name, filter_data, return_one=True):
    filter_param = filter_data
    filter_param.update(
        {
            "status": Status.ACTIVE
        }
    )
    queryset = model_name.objects.filter(
        **filter_param
    ).exclude(
        is_global=PublishStatus.PRIVATE
    )

    if queryset.exists():
        if return_one:
            # return only one record
            return queryset[0]
        # return all
        return queryset
    return None


def get_json_data_from_file(file_name):
    try:
        data = open(os.path.join(settings.REPO_DIR, file_name), 'r')
        return json.load(data)
    except Exception:
        return None

def get_csv_data_from_file(content):
    try:
        return list(csv.DictReader(codecs.iterdecode(content, 'utf-8')))
    except Exception as e:
        return None

def get_csv_data_from_temp_file(file_name):
    try:
        return list(csv.DictReader(open(os.path.join(settings.REPO_DIR, file_name), 'r')))
    except Exception as e:
        return None


def unicode_slugify(name):
    """
    Makes a slug from a given string

    :param name: any string
    :return: slug from that string
    """
    return slugify(name.lower().strip())

def get_or_create_global_object(model_name, attribute):

    obj = model_name.objects.filter(
        Q(is_global=PublishStatus.INITIALLY_GLOBAL) | Q(
            is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
        status=Status.ACTIVE,
        **attribute
    )[:1]

    if obj.count() == 0:
        try:
            obj = model_name.objects.create(
                status=Status.ACTIVE,
                is_global=PublishStatus.INITIALLY_GLOBAL,
                **attribute
            )
            obj.save()
        except (AssertionError, IntegrityError):
            return None
    else:
        obj = obj[0]

    return obj


def get_or_create_object(model_name, attribute):

    obj = model_name.objects.filter(
        status=Status.ACTIVE,
        **attribute
    )[:1]

    if obj.count() == 0:
        try:
            obj = model_name.objects.create(
                status=Status.ACTIVE,
                **attribute
            )
            obj.save()
        except (AssertionError, IntegrityError):
            return None
    else:
        obj = obj[0]

    return obj


def _create_object(model_name, attribute=None):
    """[create model object from passing attribute]

    Arguments:
        model_name {[object]} -- [Model Object, Name]

    Keyword Arguments:
        attribute {[dict]} -- [attributes of a model] (default: {None})

    Returns:
        [instance] -- [created instance]
    """

    if model_name and attribute:
        try:
            obj = model_name.objects.create(

                **attribute
            )
            obj.save()
            return obj
        except Exception as exception:
            logger.error(exception)
            return None
    return None


def print_all_organization_name(organization_type=None):

    from core.models import Organization

    if organization_type is None:
        organizations = Organization.objects.filter(
            status=Status.ACTIVE,
        ).order_by('id')
    else:
        organizations = Organization.objects.filter(
            status=Status.ACTIVE,
            type=organization_type
        ).order_by('id')
    logger.info("***********************************************************")
    logger.info("ID ----- NAME")
    for organization in organizations:
        logger.info("{}       {}".format(organization.id, organization.name))

    logger.info("***********************************************************")

def get_date_input(label):
    label = "{} (Eg : 13-07-2017) : ".format(label)
    date_input = str(input(label))
    try:
        return timezone.make_aware(datetime.strptime(date_input, '%d-%m-%Y'))
    except ValueError:
        logger.info("{} is a incorrect format".format(date_input))

def get_organization_by_input_id(organization_type=None):

    from core.models import Organization
    print_all_organization_name(organization_type)
    try:
        organization_id = input("GIVE ORGANIZATION ID : ")
    except NameError:
        return get_organization_by_input_id(organization_type)

    organization_name = input("NAME OF ORGANIZATION (CASE SENSITIVE) : ")
    try:
        if organization_type is None:
            return Organization.objects.get(
                id=organization_id,
                name=organization_name,
                status=Status.ACTIVE
            )
        else:
            return Organization.objects.get(
                id=organization_id,
                name=organization_name,
                status=Status.ACTIVE,
                type=organization_type
            )

    except Organization.DoesNotExist:
        return get_organization_by_input_id(organization_type)

def get_storepoint_by_id(organization_instance, msg="GIVE STOEPOINT ID : "):

    from pharmacy.models import StorePoint

    storepoints = StorePoint.objects.filter(
        status=Status.ACTIVE,
        organization=organization_instance
    )

    logger.info("***********************************************************")
    logger.info("ID ----- NAME")
    for storepoint in storepoints:
        logger.info("{}       {}".format(storepoint.id, storepoint.name))

    logger.info("***********************************************************")

    try:
        storepoint_id = input(msg)
    except NameError:
        return get_storepoint_by_id(organization_instance, msg)

    try:
        return StorePoint.objects.get(
            id=storepoint_id,
            status=Status.ACTIVE,
            organization=organization_instance
        )
    except StorePoint.DoesNotExist:
        return get_storepoint_by_id(organization_instance, msg)

def is_agree_to_proceed():
    try:
        choice = input('Do you want to continue? [Y/n] ')
        return True if choice.lower() == 'y' else False
    except NameError:
        return False

def print_all_account_name(organization_instance):
    from account.models import Accounts

    accounts = Accounts.objects.filter(
        organization=organization_instance,
        status=Status.ACTIVE,
    )

    logger.info("***********************************************************")
    logger.info("ID ----- NAME")
    for item in accounts:
        logger.info("{}       {}".format(item.id, item.name))

    logger.info("***********************************************************")


def print_all_company_name(organization_instance, model):

    items = model.objects.filter(
        organization=organization_instance,
        status=Status.ACTIVE,
    )

    logger.info("***********************************************************")
    logger.info("ID ----- NAME ----- HAS CLONE")
    for item in items:
        logger.info("{}       {}      {}".format(
            item.id, item.name, 'YES' if item.clone else 'NO'))

    logger.info("***********************************************************")


def print_all_employee_name(organization_instance):
    from core.models import PersonOrganization
    from core.enums import PersonGroupType

    person_organizations = PersonOrganization.objects.filter(
        organization=organization_instance,
        status=Status.ACTIVE,
        person_group=PersonGroupType.EMPLOYEE
    )

    logger.info("***********************************************************")
    logger.info("ID ----- NAME")
    for item in person_organizations:
        logger.info("{}       {}".format(item.id, item.get_full_name()))

    logger.info("***********************************************************")

def get_employee_person_organization_by_input_id(organization_instance, msg):
    from core.models import PersonOrganization

    print_all_employee_name(organization_instance)

    try:
        employee_id = input(msg)
    except NameError:
        return None

    try:
        return PersonOrganization.objects.get(
            id=employee_id,
            organization=organization_instance,
            status=Status.ACTIVE
        )
    except PersonOrganization.DoesNotExist:
        return get_employee_person_organization_by_input_id(organization_instance, msg)

def get_account_by_input_id(organization_instance, msg):
    from account.models import Accounts

    print_all_account_name(organization_instance)

    try:
        accounts_id = input(msg)
    except NameError:
        return None

    try:
        return Accounts.objects.get(
            id=accounts_id,
            organization=organization_instance,
            status=Status.ACTIVE
        )
    except Accounts.DoesNotExist:
        return get_account_by_input_id(organization_instance, msg)

def get_manufacturing_companies_by_input_id(organization_instance, msg, model):

    print_all_company_name(organization_instance, model)

    try:
        ids = [int(item) for item in input(msg).split(' ') if int(item)]
    except ValueError:
        return get_manufacturing_companies_by_input_id(organization_instance, msg, model)
    if not ids:
        return get_manufacturing_companies_by_input_id(organization_instance, msg, model)

    try:
        queryset = model.objects.filter(
            organization=organization_instance,
            status=Status.ACTIVE,
            id__in=ids,
            clone__isnull=False,
        )
        logger.info("***************************************")
        replacing_id_list = []
        for company in queryset:
            logger.info("[#{} {}] Will Be Replaced By => [#{} {}]".format(
                company.id, company.name, company.clone.id, company.clone.name))
            replacing_id_list.append({'old': company.id, 'new': company.clone.id})
        if replacing_id_list and is_agree_to_proceed():
            return replacing_id_list
        return []
    except model.DoesNotExist:
        return get_manufacturing_companies_by_input_id(organization_instance, msg, model)

def prepare_date_filter_with_period_value(request):
    period_value = request.query_params.get('period', None)
    days = request.query_params.get('days', None)

    if period_value is not None:
        start_date = str(get_date_from_period(period_value))
        end_date = str(DT.date.today())
    elif days is not None:
        start_date = DT.date.today() + DT.relativedelta(days=-int(days))
        end_date = DT.date.today()
    else:
        start_date = request.query_params.get('start', None)
        end_date = request.query_params.get('end', None)
    start_date = DT.datetime.combine(
        DT.datetime.strptime(start_date, '%Y-%m-%d'), DT.time.min)
    end_date = DT.datetime.combine(
        DT.datetime.strptime(end_date, '%Y-%m-%d'), DT.time.max)
    start_date = timezone.make_aware(
        start_date, timezone.get_current_timezone())
    end_date = timezone.make_aware(
        end_date, timezone.get_current_timezone())
    return {
        'start': start_date,
        'end': end_date
    }

def get_storepoint_by_product(products):
    from django.db.models import Prefetch
    from pharmacy.models import Product, StorePoint, Stock

    if isinstance(products, (int)):
        # products_id a number
        stocks = Stock.objects.filter(
            product__pk=products
        )
    elif isinstance(products, (Product)):
        # products_id an instante of Product class
        stocks = Stock.objects.filter(
            product__pk=products.pk
        )

    elif isinstance(products, (list)):
        # products_id is list
        # listing all stock associated with products of given list
        stocks = Stock.objects.filter(
            product__pk__in=products
        )
    else:
        return None

    return StorePoint.objects.filter(
        status=Status.ACTIVE
    ).prefetch_related(
        Prefetch(
            'store_list',
            queryset=stocks,
            to_attr='problamatic_stock'
        )
    )


def custom_elastic_rebuild(model_string, queryset_filter):
    from common.tasks import custom_elastic_rebuild_on_bg
    custom_elastic_rebuild_on_bg.apply_async(
        (model_string, queryset_filter),
        countdown=5,
        retry=True, retry_policy={
            'max_retries': 10,
            'interval_start': 0,
            'interval_step': 0.2,
            'interval_max': 0.2,
        }
    )

def custom_elastic_delete(model_string, target_id):
    from common.tasks import custom_elastic_delete_on_bg
    custom_elastic_delete_on_bg.apply_async(
        (model_string, target_id),
        countdown=5,
        retry=True, retry_policy={
            'max_retries': 10,
            'interval_start': 0,
            'interval_step': 0.2,
            'interval_max': 0.2,
        }
    )

def pk_extractor(queryset):
    '''
        this method return  pk of every item of a queryset as list
    '''
    instances_pk = []
    for item in queryset:
        if isinstance(item, int):
            instances_pk.append(item)
        else:
            instances_pk.append(item.id)
    return instances_pk


def get_first_obj_by_name_and_id(model, name, _id):
    '''
    Get an object by its model, name and id
    Parameters
    ----------
    name : string
        name is a attribute in model
    _id : integer
        the pk of the object

    Raises
    ------
    No error is raised by this method

    Returns
    -------
    obj
        first object of queryset if queryset found, otherwise none
    '''

    data = model.objects.filter(
        pk=_id,
        name=name,
        status=Status.ACTIVE
    )
    if data.exists():
        return data.first()
    return None

def get_num_or_zero_from_dict(data, key):
    try:
        return float(data[key])
    except (ValueError, KeyError, TypeError):
        return 0

def get_str_or_none_from_dict(data, key):
    try:
        if data[key] and data[key] != '':
            return data[key]
        return None
    except (ValueError, KeyError):
        return None

def get_str_or_na_from_dict_or_blank(data, key, blank=False):
    try:
        if data[key] and data[key] != '':
            return data[key]
        return 'N/A' if not blank else ''
    except (ValueError, KeyError):
        return 'N/A' if not blank else ''

def get_date_or_today_from_dict(data, key):
    try:
        if data[key] and data[key] != '':
            date_str = data[key]
            date_obj = datetime.strptime(date_str, '%Y-%d-%m')
            return date_obj
        return date.today()
    except (ValueError, KeyError):
        return date.today()

def generate_phone_no_for_sending_sms(phone_no=""):
    country_code = "880"
    if phone_no:
        phone_no = "{}{}".format(country_code, phone_no[-10:])
    return phone_no

def get_key_by_enum_value(_enum, value=0):
    """[get enum class and return key by value]

    Arguments:
        _enum {[enum class]} -- [specific enum class]

    Keyword Arguments:
        value {value} -- [enum value] (default: {0})

    Returns:
        [string] -- [enum key]
    """
    enum_dict = _enum.get_as_dict()
    if _enum.is_valid_value(value):
        return list(enum_dict)[list(enum_dict.values()).index(value)].capitalize()
    return None

def to_boolean(value=False):
    """[Takes string or boolean and return boolean]

    Keyword Arguments:
        value {bool} -- [description] (default: {False})

    Returns:
        [Boolean] -- [Boolean value]
    """
    return value in (True, "True", "true")


def is_allowed_to_update_queueing_item_value(setting, product):
    if setting.overwrite_order_mode_by_product:
        order_mode = product.order_mode
    else:
        order_mode = setting.allow_order_from
    return False if order_mode == AllowOrderFrom.OPEN else True

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

def populate_es_index(model_string, queryset_filter=None, cli=False):
    from yaspin import yaspin
    from common.tasks import get_documents
    queryset_filter = {} if queryset_filter is None else queryset_filter
    for doc in get_documents(model_string):
        qs = doc().get_queryset(queryset_filter)
        message = f"Updated search index for {model_string} with filter {queryset_filter}, Total rows: {qs.count()}"
        if cli:
            with yaspin(text=message, color="green") as spinner:
                doc().update(qs)
                spinner.ok("✅ ")
        else:
            doc().update(qs)
            logger.info(message)

def change_key_mappings(data, key_mappings):
    try:
        for item in data:
            for key, value in key_mappings.items():
                item[value] = item.pop(key)
        return data
    except:
        return data

def send_log_alert_to_slack_or_mattermost(message):
    from common.tasks import send_message_to_slack_or_mattermost_channel_lazy
    send_message_to_slack_or_mattermost_channel_lazy.delay(
        os.environ.get("HOS_LOGGER_CHANNEL_ID", ""),
        message
    )

def send_message_to_mattermost_by_channel_id(channel_id, message):
    from common.tasks import send_message_to_slack_or_mattermost_channel_lazy

    send_message_to_slack_or_mattermost_channel_lazy.delay(
        channel_id,
        message
    )

def send_top_sheet_activity_alert_to_slack_or_mattermost(message):
    from common.tasks import send_message_to_slack_or_mattermost_channel_lazy
    send_message_to_slack_or_mattermost_channel_lazy.delay(
        os.environ.get("TOP_SHEET_ACTIVITY_CHANNEL_ID", ""),
        message
    )


def get_request_object():
    import inspect
    stacks = inspect.stack()[::-1]
    for frame_record in stacks:
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break
    else:
        request = None

    return request


def get_enum_key_by_value(enum_class, value):
    enum_class_dict = enum_class.get_as_dict()
    if value in enum_class_dict.values():
        return list(enum_class.get_as_dict())[list(enum_class.get_as_dict().values()).index(value)]
    return None
