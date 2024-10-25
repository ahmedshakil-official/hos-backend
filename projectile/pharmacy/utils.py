# for python3 compatibility
from __future__ import division

from functools import reduce

from future.builtins import round

import logging
import math
import collections
import operator
import pandas as pd
import datetime
import time, os
from validator_collection import checkers

from django.db.models.functions import Coalesce
from django.db.models import Sum, Value, Q, Case, When, F, DateField
from django.db.models.query import QuerySet
from django.utils import timezone
from django.core.cache import cache

from common.enums import Status, PublishStatus, DiscardType
from common.utils import (
    get_ratio,
    validate_uuid4,
    convert_utc_to_local,
    get_date_obj_from_date_str,
)
from common.cache_keys import CART_GROUP_CACHE_KEY
from core.models import Organization
from core.enums import AllowOrderFrom
from core.helpers import get_order_ending_time
from expo_notification.tasks import (
    send_push_notification_to_mobile_app,
    send_push_notification_to_mobile_app_by_org,
)
from elasticsearch_dsl import Q as esQ
from .enums import (
    StockIOType,
    PurchaseType,
    SalesInactiveType,
    DistributorOrderType,
    OrderTrackingStatus,
)
from .models import (
    Product,
    StorePoint,
    Stock,
    StockIOLog,
    Purchase,
    EmployeeAccountAccess,
    EmployeeStorepointAccess,
    OrganizationWiseDiscardedProduct,
)
from .helpers import (
    stop_inventory_signal,
    start_inventory_signal,
)

from core.helpers import get_user_profile_details_from_cache

logger = logging.getLogger(__name__)

def get_latest_io_logs_of_stocks(self, model, store_point):
    stocks = model.objects.filter(
        organization=self.request.user.organization,
        stock__store_point__alias=store_point,
        adjustment__isnull=True,
        rate__gt=0
    )

    latest_sales = stocks.values_list('id', flat=True).filter(
        status=Status.ACTIVE,
        type=StockIOType.OUT
    ).order_by('-id')
    latest_sales = model.objects.filter(
        id__in=list(latest_sales)
    )

    latest_purchase = stocks.values_list('id', flat=True).filter(
        status=Status.ACTIVE,
        type=StockIOType.INPUT
    ).order_by('-id')
    latest_purchase = model.objects.filter(
        id__in=list(latest_purchase)
    )

    latest_order = stocks.values_list('id', flat=True).filter(
        status=Status.PURCHASE_ORDER,
        type=StockIOType.INPUT
    ).order_by('-id')
    latest_order = model.objects.filter(
        id__in=list(latest_order)
    )

    return {
        'sales': latest_sales,
        'purchase': latest_purchase,
        'order': latest_order
    }

def prepare_for_sales_graph(data):
    stores = [item['store'] for item in data]
    stores = set(stores)
    graph = []
    for store in stores:
        graph_data = [
            [
                item['date'], item['value']
            ] for item in data if item['store'] == store
        ]
        graph.append({
            'name': store,
            'data': graph_data,
        })
    return graph


def get_product_store_wise_stock(stock, store_point, model):
    _stock = model.objects.get(pk=stock)
    required_stock = model.objects.get(
        product=_stock.product,
        store_point=store_point,
        status=Status.ACTIVE,
    )
    return required_stock.id


# Batchwise stock of a product
def get_batch_wise_stock(stock, batch='N/A'):
    if isinstance(stock, int):
        stock = Stock.objects.get(id=stock)
    # Batchwise summation of product that IN
    stock_io = StockIOLog.objects.filter(
        status=Status.ACTIVE,
        stock=stock,
        batch=batch,
    ).values('stock').aggregate(
        qty_in=Coalesce(Sum(Case(When(
            type=StockIOType.INPUT, then=F('quantity')))), 0.00),
        qty_out=Coalesce(Sum(Case(When(
            type=StockIOType.OUT, then=F('quantity')))), 0.00)
    )
    # Subtract stock IN and stock OUT to get batchwise stock of a product
    stock_qty = stock_io['qty_in'] - stock_io['qty_out']
    return stock_qty


def update_stock_calculated_price(self, purchase_id):
    purchase = Purchase.objects.values(
        'status', 'purchase_type', 'is_sales_return', 'discount',
        'round_discount', 'vat_total', 'tax_total', 'amount', 'transport',
    ).get(id=purchase_id)

    if purchase['status'] == Status.ACTIVE and purchase['purchase_type'] == PurchaseType.PURCHASE \
        and not purchase['is_sales_return']:
        io_logs = StockIOLog.objects.filter(
            purchase=purchase_id, status=Status.ACTIVE
        ).values(
            'stock', 'quantity', 'discount_total', 'vat_total', 'tax_total',
            'secondary_unit_flag', 'conversion_factor', 'rate'
        )
        productwise_vat_tax = io_logs.aggregate(
            discount_total=Coalesce(Sum('discount_total'), 0.00),
            vat_total=Coalesce(Sum('vat_total'), 0.00),
            tax_total=Coalesce(Sum('tax_total'), 0.00),
        )

        dristributed_discount = purchase['discount'] - purchase['round_discount'] - \
            productwise_vat_tax['discount_total']
        dristributed_vat = purchase['vat_total'] - \
            productwise_vat_tax['vat_total']
        dristributed_tax = purchase['tax_total'] - \
            productwise_vat_tax['tax_total']
        dristributed_transport = purchase['transport']

        distributed_total_amount = dristributed_vat + dristributed_tax +\
            dristributed_transport - dristributed_discount

        for log in io_logs:
            try:
                trade_price = log['rate'] / log['conversion_factor'] if log['secondary_unit_flag']\
                    else log['rate']
            except ZeroDivisionError:
                trade_price = 0
            ratio_of_additional_cost = get_ratio(
                purchase['amount'] - purchase['tax_total'],
                trade_price * log['quantity']
            )

            vat_per_item = log['vat_total'] / log['quantity']
            tax_per_item = log['tax_total'] / log['quantity']
            discount_per_item = log['discount_total'] / log['quantity']

            calculated_price = trade_price + vat_per_item + tax_per_item + \
                (((distributed_total_amount/100)*ratio_of_additional_cost) /
                 log['quantity']) - discount_per_item

            stock_calculated_price = round(calculated_price, 4)
            stock_calculated_price_organization_wise = \
                round(calculated_price, 4)

            Stock.objects.filter(pk=log['stock']).update(
                calculated_price=stock_calculated_price,
                calculated_price_organization_wise=stock_calculated_price_organization_wise
            )

def create_item_with_clone_and_replace_clone_items(
        self, request, field_name, model_name):
    """
    takes:
        request, field name that will update and related model name

    check clone item is available or not
    if available then find data from related model
    and update with created item

    returns:
        serialize data
    """
    clone_item = request.data.get('clone_item', None)
    if clone_item:
        arguments = {field_name: clone_item['parent']}
    serializer = self.get_serializer_class()(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid(raise_exception=True):
        if clone_item:
            serializer.save(
                entry_by=self.request.user,
                organization=self.request.user.organization,
                clone_id=clone_item['parent'],
            )
            filter_data = model_name.objects.filter(
                status=Status.ACTIVE,
                organization=self.request.user.organization,
                **arguments
            )
            field_name_id = field_name + '_id'
            for item in filter_data:
                if hasattr(item, field_name_id):
                    setattr(item, field_name_id, serializer.data['id'])
                    item.save(update_fields=[field_name, ])
        else:
            serializer.save(
                entry_by=self.request.user,
                organization=self.request.user.organization,
            )
        return serializer
    return None


def check_is_user_admin_or_superuser(self):
    """
    check is current user is admin or super
    """
    # is_superuser = self.request.user.is_superuser
    # is_admin = PersonOrganizationGroupPermission.objects.filter(
    #     person_organization__organization=self.request.user.organization_id,
    #     status=Status.ACTIVE,
    #     person_organization__person__alias=self.request.user.alias,
    #     permission__name='Admin'
    # ).exists()
    # return True if is_superuser or is_admin else False
    return self.request.user.is_admin_or_super_admin()


def prepare_filter_arguments(id_list, is_search=False, *fields):
    """
    takes: list of id, a boolean field and list of model field name
    return: filter arguments
    """
    from functools import reduce
    arguments = Q() if not is_search else esQ()
    argument_list = []
    for field_name in fields:
        # add __ with field name to filter by id
        field_name += '__' if field_name else ''
        if is_search:
            argument_list.append(
                esQ('terms', **{field_name + 'id': id_list})
            )
        else:
            argument_list.append(
                Q(**{field_name + 'id__in': id_list})
            )
    arguments = reduce(operator.or_, argument_list)
    return arguments


def filter_queryset_for_primary(queryset, permitted_id_list, is_search):
    if is_search:
        queryset = queryset.filter(esQ('terms', id=permitted_id_list))
    else:
        queryset = queryset.filter(id__in=permitted_id_list)
    return queryset


def filter_data_by_user_permitted_store_points(self, queryset, *field_name, **kwargs):
    """
    takes: queryset and model field name
    get user permitted store point id list for non admin or blank list
    filter queryset by those store point ids
    return: queryset
    """
    primary = kwargs.get('primary')
    is_search = False
    if not isinstance(queryset, QuerySet):
        is_search = True
    fields = []
    if field_name:
        fields += field_name
    else:
        fields = ['store_point']

    is_admin_or_su = check_is_user_admin_or_superuser(self)
    store_points = []
    if not is_admin_or_su:
        person_organization = self.request.user.get_person_organization_for_employee()
        store_points = person_organization.get_user_permitted_data(
            EmployeeStorepointAccess, 'store_point'
        )

    if store_points or not is_admin_or_su:
        if primary:
            queryset = filter_queryset_for_primary(queryset, store_points, is_search)
        else:
            args = prepare_filter_arguments(store_points, is_search, *fields)
            queryset = queryset.filter(*(args, ))
    return queryset


# def get_user_permitted_account(self):
#     """
#     take self
#     for non admin user return list of permitted account ids
#     for admin or super user return blank list
#     return list
#     """
#     accounts = []
#     is_admin_or_super_admin = check_is_user_admin_or_superuser(self)
#     if not is_admin_or_super_admin:
#         accounts = EmployeeAccountAccess.objects.filter(
#             organization=self.request.user.organization,
#             status=Status.ACTIVE,
#             access_status=True,
#             employee__alias=self.request.user.alias,
#         ).values_list('account', flat=True)
#     return list(accounts)


def filter_data_by_user_permitted_accounts(self, queryset, *args, **kwargs):
    """
    takes: queryset
    get user permitted account id list for non admin or blank list
    filter queryset by those account ids
    return: queryset
    """
    accounts = []
    primary = kwargs.get('primary')
    is_search = False
    if not isinstance(queryset, QuerySet):
        is_search = True
    is_admin_or_super_admin = check_is_user_admin_or_superuser(self)
    if not is_admin_or_super_admin:
        person_organization = self.request.user.get_person_organization_for_employee()
        accounts = person_organization.get_user_permitted_data(
            EmployeeAccountAccess, 'account'
        )
    if accounts or not is_admin_or_super_admin:
        if primary:
            if is_search:
                queryset = queryset.filter(esQ('terms', id=accounts))
            else:
                queryset = queryset.filter(id__in=accounts)
        else:
            args = prepare_filter_arguments(accounts, is_search, 'accounts')
            queryset = queryset.filter(*(args, ))
    return queryset


def construct_product_object_from_dictionary(obj, removable_prefix=''):
    """[get plain object and return like the Product object]
    Arguments:
        obj {[dict]} -- [description]
    """
    if removable_prefix:
        for key in list(obj):
            obj[key.replace('stock__', '')] = obj.pop(key)
    return {
        'id': obj.get('product', None),
        'name': obj.get('product__name', None),
        'strength': obj.get('product__strength', None),
        'alias': obj.get('product__alias', None),
        'purchase_price': obj.get('product__purchase_price', None),
        'trading_price': obj.get('product__trading_price', None),
        'form': {
            'name': obj.get('product__form__name', None)
        },
        'generic': {
            'name': obj.get('product__generic__name', None),
        },
        'manufacturing_company': {
            'name': obj.get('product__manufacturing_company__name', None)
        },
        'subgroup' : {
            'name': obj.get('product__subgroup__name', None),
            'product_group': {
                'type': obj.get('product__subgroup__product_group__type', None),
                'name': obj.get('product__subgroup__product_group__name', None)
            }
        }
    }

def construct_store_point_object_from_dictionary(obj, fields_dict=None):
    """[get plain object and return like the storepoint object]
    Arguments:
        obj {[dict]} -- [description]
    """
    default_fields_dict = {
        'id': 'store_point',
        'alias': 'store_point__alias',
        'name': 'store_point__name'
    }
    fields_dict = fields_dict if fields_dict else default_fields_dict
    data = {key: obj.get(value, None) for key, value in fields_dict.items()}
    return data

def construct_stock_object_from_dictionary(obj):
    """[get plain object and return like the Stock object]
    Arguments:
        obj {[dict]} -- [description]
    """
    return {
        'store_point': {
            'id': obj.get('stock__store_point', None),
            'name': obj.get('stock__store_point__name', None)
        },
        'product': {
            'id': obj.get('stock__product', None),
            'name': obj['stock__product__name'],
            'strength': obj.get('stock__product__strength', None),
            'alias': obj['stock__product__alias'],
            'purchase_price': obj.get('stock__product__purchase_price', None),
            'trading_price': obj.get('stock__product__trading_price', None),
            'form': {
                'name': obj['stock__product__form__name']
            },
            'generic': {
                'name': obj.get('stock__product__generic__name', None),
            },
            'manufacturing_company': {
                'name': obj['stock__product__manufacturing_company__name']
            },
            'subgroup' : {
                'name': obj.get('stock__product__subgroup__name', None),
                'product_group': {
                    'type': obj['stock__product__subgroup__product_group__type'],
                    'name': obj.get('stock__product__subgroup__product_group__name', None)
                }
            }
        },
        'stock': obj.get('stock__stock', 0),
        'id': obj.get('stock__id', None),
        'purchase_rate': obj.get('stock__purchase_rate', 0),
        'sales_rate': obj.get('stock__sales_rate', 0),
        'calculated_price': obj.get('stock__calculated_price', 0),
        'minimum_stock': obj.get('stock__minimum_stock', 0),
    }


def filter_list_of_items(queryset, field_name, values):
    if values:
        value_list = [item for item in values.split(',')]
        lookup = '__'.join([field_name, 'in'])
        queryset = queryset.filter(**{lookup: value_list})
    return queryset

def validate_uuid4_list(params, key):
    valid_uuid4_list = []
    try:
        for uuid4_data in str(params[key]).split(","):
            if validate_uuid4(uuid4_data):
                valid_uuid4_list.append(uuid4_data)
        return valid_uuid4_list
    except KeyError:
        return []

def stock_specific_attribute_filter(params):
    custom_filter = {}

    for key in params.keys():
        uuid4_list = validate_uuid4_list(params, key)
        if uuid4_list:
            if key == "companies":
                custom_filter["product__manufacturing_company__alias__in"] = \
                    uuid4_list

            if key == "store_points":
                custom_filter["store_point__alias__in"] = uuid4_list

            if key == "products":
                custom_filter["product__alias__in"] = uuid4_list

            if key == "product_forms":
                custom_filter["product__form__alias__in"] = uuid4_list

            if key == "product_subgroups":
                custom_filter["product__subgroup__alias__in"] = uuid4_list

            if key == "product_groups":
                custom_filter["product__subgroup__product_group__alias__in"] = uuid4_list

    return custom_filter


def merge_two_products(organization, primary_product, mergeable_product):
    """[Merge a mergeable product to a primary product]
    Arguments:
        organization {[type]} -- [Organization ID]
        primary_product {[type]} -- [Primary Product ID (Survived Product)]
        mergeable_product {[type]} -- [Mergeable Product ID (Merged Product)]
    """
    is_mergable = False
    try:
        # product that want to keep
        primary = Product.objects.get(
            id=primary_product, status=Status.ACTIVE)
    except Product.DoesNotExist:
        logger.error("PRIMARY PRODUCT IS NOT ACTIVE !")
        return
    try:
        # clone product that will inactive
        secondary = Product.objects.get(
            id=mergeable_product, status=Status.ACTIVE)
    except Product.DoesNotExist:
        logger.error("MERGEABLE PRODUCT IS NOT ACTIVE !")
        return

    # stoping all signal associated  with inventory
    stop_inventory_signal()

    # finding all storepoint of this organization
    storepoints = StorePoint.objects.filter(
        organization=organization,
    )

    for store in storepoints:

        # we need to find stock associated with secondary product for every storepoint
        # this will get replaced
        secondary_stock = Stock().get_stock_by_store_and_product(store, secondary)

        # we need to find stock associated with primary product for every storepoint
        # secondary stock will be replaced by this stock
        primary_stock = Stock().get_stock_by_store_and_product(store, primary)
        if primary_stock:
            is_mergable = True

        if primary_stock is not None and secondary_stock is not None:

            # replacing all stock of secondary stock with primary_stock
            StockIOLog().replace_stock_in_stock_io(secondary_stock, primary_stock)
            secondary_stock.status = Status.INACTIVE
            secondary_stock.save()

            # stock of primary product will increase
            primary_stock.stock = primary_stock.stock + secondary_stock.stock
            primary_stock.save()
    if is_mergable:
        # add necessary discarded entry
        discarded_entry = OrganizationWiseDiscardedProduct.objects.create(
            product=primary,
            parent=secondary,
            entry_type=DiscardType.MERGE,
            organization_id=organization
        )
        discarded_entry.save()

        if secondary.is_global == PublishStatus.PRIVATE:
            # make secondary product status inactive
            secondary.status = Status.INACTIVE
            secondary.save()

    # starting all signal that is associated with inventory
    start_inventory_signal()
    logger.info("MERGED PRODUCT #{} {} TO #{} {} SUCCESSFULLY!".format(
        secondary.id, secondary.full_name, primary.id, primary.full_name))
    return is_mergable

def datetime_from_utc_to_local(utc_datetime):
    # return utc_datetime
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def get_discount_from_offer_rules(order_instance, amount_total):
    """
    Get discount from offer rules
    """
    max_discount_data = {
        "discount": 0,
        "percentage": True,
        "discount_amount": 0
    }
    max_rule_discount_amount = 0
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
    offer_rules = order_instance.organization.offer_rules
    order_date = order_instance.purchase_date

    for rule in offer_rules:
        max_rule_discount_amount = 0
        max_discount_data = {
            "discount": 0,
            "percentage": True,
            "discount_amount": 0
        }
        start_date = rule.get('start_date', '')
        end_date = rule.get('end_date', '')
        min_order_amount = rule.get('min_order_amount', 0) or 0
        discount_in_percentage = rule.get('discount_in_percentage', 0) or 0
        discount_in_flat = rule.get('discount_in_flat', 0) or 0

        if checkers.is_datetime(start_date) and checkers.is_datetime(end_date):
            start = datetime.datetime.strptime(start_date, DATE_TIME_FORMAT)
            end = datetime.datetime.strptime(end_date, DATE_TIME_FORMAT)
            order_date = datetime.datetime.strptime(
                str(datetime_from_utc_to_local(order_date).replace(tzinfo=None)),
                '%Y-%m-%d %H:%M:%S'
            ).strftime(DATE_TIME_FORMAT)
            order_date = datetime.datetime.strptime(order_date, DATE_TIME_FORMAT)

            if start <= order_date <= end and amount_total >= min_order_amount:
                discount = discount_in_percentage if discount_in_percentage > 0 else discount_in_flat
                percentage = True if discount_in_percentage > 0 else False
                rule_discount_amount = discount if not percentage else (discount * amount_total) / 100
                if rule_discount_amount > max_rule_discount_amount:
                    max_rule_discount_amount = rule_discount_amount
                    max_discount_data = {
                        "discount": discount,
                        "percentage": percentage,
                    }

    return max_discount_data, max_rule_discount_amount


def get_additional_discount_data(amount_total, is_queueing_order=False, order_instance=None):
    if amount_total > 30000:
        additional_discount = 2
    elif 30000 > amount_total >= 20000:
        additional_discount = 1.75
    elif 20000 > amount_total >= 15000:
        additional_discount = 1.50
    elif 15000 > amount_total >= 10000:
        additional_discount = 1.25
    elif 10000 > amount_total >= 5000:
        additional_discount = 1.15
    elif 5000 > amount_total >= 2500:
        additional_discount = 1
    elif amount_total < 2500 and is_queueing_order:
        additional_discount = 0.50
    else:
        additional_discount = 0
    discount_from_rule, discount_amount_from_rule  = get_discount_from_offer_rules(
        order_instance,
        amount_total,
    )
    _discount_amount = (amount_total * additional_discount) / 100
    if discount_amount_from_rule > _discount_amount:
        return discount_from_rule
    return {
        "discount": additional_discount,
        "percentage": True,
    }

def send_push_notification_for_additional_discount(user_id, entry_by_id, additional_discount, order_id):
    notification_title = "Cashback !!!"
    notification_body = f"Congratulation, You will get BDT {round(additional_discount, 2)} as additional cashback on #{order_id}."
    notification_data = {}
    # Send push notification to mobile device
    if additional_discount > 0:
        send_push_notification_to_mobile_app.delay(
            user_id,
            title=notification_title,
            body=notification_body,
            data=notification_data,
            entry_by_id=entry_by_id
        )


def get_is_queueing_item_value(orderable_stock, product_order_mode, setting = None):
    if setting is None:
        org_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        settings_cache_key = f"organization_settings_{org_id}"
        settings_from_cache = cache.get(settings_cache_key)
        if settings_from_cache is not None:
            setting = settings_from_cache
        else:
            try:
                setting = Organization.objects.only('id').get(pk=org_id).get_settings()
            except Organization.DoesNotExist:
                setting = Organization.objects.only('id').get(pk=org_id).get_settings()

    if setting.overwrite_order_mode_by_product:
        order_mode = product_order_mode
    else:
        order_mode = setting.allow_order_from
        # if organization order mode is stock and open then we consider product order mode as
        # current order mode, so we taking product order mode
        if setting.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN:
            logger.info(f"For organization order mode STOCK_AND_OPEN using product order mode: {product_order_mode}")
            order_mode = product_order_mode

    if order_mode == AllowOrderFrom.OPEN:
        return False
    else:
        return orderable_stock <= 0

def get_item_from_list_of_dict(_list, key, value):
    item = next(
        filter(
            lambda item: item[key] == value, _list
        ), {}
    )
    return item

def set_ecom_stock_from_file(stock_file_instance, lower_limit, upper_limit):
    from .helpers import stop_inventory_signal, start_inventory_signal

    stop_inventory_signal()
    try:
        stock_file = stock_file_instance
        file_name = stock_file.name
        stock_df = pd.read_csv(stock_file.content)
        data_df = stock_df[lower_limit:upper_limit]

        for index, item in data_df.iterrows():
            requesting_stock_qty = item.get('STOCK')
            stock_id = item.get('ID')

            if not math.isnan(requesting_stock_qty) and not math.isnan(stock_id):
                try:
                    stock = Stock.objects.only(
                        'id',
                        'stock',
                        'orderable_stock'
                    ).get(pk=stock_id)
                    current_orderable_stock = stock.get_current_orderable_stock(requesting_stock_qty)
                    if stock.ecom_stock != requesting_stock_qty or stock.orderable_stock != current_orderable_stock:
                        logger.info(
                            "{} PREV Q : {} CALCULATED QTY : {}".format(
                                stock.product.name.ljust(40),
                                str(stock.ecom_stock).ljust(10),
                                str(requesting_stock_qty).ljust(10)
                            )
                        )
                        stock.ecom_stock = requesting_stock_qty
                        stock.orderable_stock = current_orderable_stock
                        stock.save(update_fields=['ecom_stock', 'orderable_stock'])
                    # Check if product is_queueing_item should change or not
                    product = Product.objects.only('order_mode', 'is_queueing_item').get(pk=stock.product_id)
                    is_queueing_item_value = get_is_queueing_item_value(
                        stock.orderable_stock,
                        product.order_mode,
                    )
                    if is_queueing_item_value != product.is_queueing_item:
                        product.is_queueing_item = is_queueing_item_value
                        product.save(update_fields=['is_queueing_item'])
                        logger.info(
                            f"Set product is queueing item to {is_queueing_item_value} for stock {stock.id}."
                        )
                    stock.expire_cache()
                except Stock.DoesNotExist:
                    logger.info(
                        f"Unable to populate stocks for stock {stock.id}, Exception: {str(exception)}"
                    )
                    pass
        logger.info(f"Successfully populated stock for file {file_name}")
    except Exception as exception:
        logger.info(
            f"Unable to populate stocks for file {file_name}, Exception: {str(exception)}"
        )

    start_inventory_signal()

def get_cart_group_id(org_id):
    cache_key = f"{CART_GROUP_CACHE_KEY}{org_id}"
    group_data = cache.get(cache_key) or {}
    cart_group_id = group_data.get('cart_group_id', None)
    if cart_group_id:
        return cart_group_id
    else:
        ord_instance = Organization.objects.only('id').get(pk=org_id)
        return ord_instance.get_or_add_cart_group(set_cache=True)


def get_or_create_cart_instance(org_id, dist_id, cart_group_id, user_id, is_queueing_order = False, set_cache = False):

    cache_key =  f"cart_group_{org_id}"
    instance_key = f"cart_instance_queue_{is_queueing_order}"
    group_data = cache.get(cache_key)

    if set_cache:
        group_data = group_data if group_data else {}
        cart_instance_id = group_data.get(instance_key, None)
        if cart_instance_id:
            return cart_instance_id
    try:
        cart_instance = Purchase.objects.only('pk').get(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=org_id,
            distributor__id=dist_id,
            distributor_order_group__id=cart_group_id,
            is_queueing_order=is_queueing_order,
            distributor_order_type=DistributorOrderType.CART,
            purchase_type=PurchaseType.VENDOR_ORDER,
        )
    except Purchase.DoesNotExist:
        cart_instance = Purchase.objects.create(
            status=Status.DISTRIBUTOR_ORDER,
            organization_id=org_id,
            distributor_id=dist_id,
            distributor_order_group_id=cart_group_id,
            is_queueing_order=is_queueing_order,
            distributor_order_type=DistributorOrderType.CART,
            purchase_type=PurchaseType.VENDOR_ORDER,
            receiver_id=user_id,
        )
    except Purchase.MultipleObjectsReturned:
        cart_instance = Purchase.objects.only('pk').filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization_id=org_id,
            distributor_id=dist_id,
            distributor_order_group__id=cart_group_id,
            is_queueing_order=is_queueing_order,
            distributor_order_type=DistributorOrderType.CART,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).first()
        cart_instance_pks = Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization_id=org_id,
            distributor_id=dist_id,
            distributor_order_group__id=cart_group_id,
            is_queueing_order=is_queueing_order,
            distributor_order_type=DistributorOrderType.CART,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).values_list('pk', flat=True)
        pk_list = list(cart_instance_pks[1:])
        Purchase.objects.filter(pk__in=pk_list).update(status=Status.INACTIVE)
    # Set cache
    group_data[instance_key] = cart_instance.id
    cache.set(cache_key, group_data)
    return cart_instance if not set_cache else cart_instance.id


def get_or_set_min_order_amount_in_cache(org_id):
    cache_key = f"cart_group_{org_id}"
    organization_data = cache.get(cache_key) or {}
    if "min_order_amount" in organization_data:
        return organization_data["min_order_amount"]

    try:
        organization = Organization.objects.only(
            "min_order_amount",
        ).get(pk=org_id)
        min_order_amount = organization.min_order_amount
        organization_data["min_order_amount"] = min_order_amount
        cache.set(cache_key, organization_data)

        return min_order_amount
    except Organization.DoesNotExist:
        return None


def get_tentative_delivery_date(order_date, is_queueing_order = False):
    time_slot_str = str(get_order_ending_time())
    time_slot = datetime.datetime.strptime(time_slot_str, '%H:%M:%S').time()
    day_end = datetime.datetime.strptime("23:59:59", '%H:%M:%S').time()
    order_time = order_date.time()
    if (time_slot < order_time <= day_end):
        return (order_date + datetime.timedelta(days=2)).date() if is_queueing_order else (order_date + datetime.timedelta(days=1)).date()
    else:
        return (order_date + datetime.timedelta(days=1)).date() if is_queueing_order else order_date.date()


discount_rules = [
    {
        "min_amount": 2500,
        "discount": 1
    },
    {
        "min_amount": 5000,
        "discount": 1.15
    },
    {
        "min_amount": 10000,
        "discount": 1.25
    },
    {
        "min_amount": 15000,
        "discount": 1.50
    },
    {
        "min_amount": 20000,
        "discount": 1.75
    },
    {
        "min_amount": 30000,
        "discount": 2
    },

]

def get_discount_rules():
    return discount_rules


def get_minimum_order_amount():
    return min(rule['min_amount'] for rule in discount_rules)


def get_discount_for_cart_and_order_items(cart_grand_total, rounding_off=True, customer_org_id=None):
    from common.healthos_helpers import CustomerHelper

    amount_to_reach_next_discount_level = 0
    current_discount_percentage = 0
    current_discount_amount = 0
    next_discount_percentage = 0
    next_discount_amount = 0
    for rule in discount_rules:
        if cart_grand_total >= rule["min_amount"]:
            current_discount_percentage = rule["discount"]
            current_discount_amount = (cart_grand_total * current_discount_percentage) / 100
            if rounding_off:
                current_discount_amount = round(current_discount_amount)
        else:
            amount_to_reach_next_discount_level = round(rule["min_amount"] - cart_grand_total)
            next_discount_percentage = rule["discount"]
            next_discount_amount = (rule["min_amount"] * next_discount_percentage) / 100
            if rounding_off:
                next_discount_amount = round(next_discount_amount)
            break
    # If customer organization have dynamic discount enabled remove the additional discount /
    # Discount Progress bar in ecom app
    if customer_org_id is not None:
        customer_helper = CustomerHelper(customer_org_id)
        discount_rate_factor = customer_helper.get_cumulative_discount_factor()
        # If discount rate factor is greater than 0 make the progress bar hidden in ecom app
        if discount_rate_factor:
            current_discount_percentage = 0
            next_discount_percentage = 0
    return {
        "amount_to_reach_next_discount_level": amount_to_reach_next_discount_level,
        "current_discount_percentage": current_discount_percentage,
        "current_discount_amount": current_discount_amount,
        "next_discount_percentage": next_discount_percentage,
        "next_discount_amount": next_discount_amount
    }


def get_fields_where_value_is_not_null(queryset, fields, values):
    values = values.split(',')
    filters = []
    for value in values:
        if value in fields:
            filters.append(Q(**{value + '__isnull': False}))
        else:
            pass
    if filters:
        return queryset.filter(reduce(operator.or_, filters))

    return queryset


def delete_order_list_from_cache(order_ids):
    from common.cache_keys import ORDER_LIST_CACHE_KEY
    from common.tasks import cache_expire_list
    order_list_cache_key = ORDER_LIST_CACHE_KEY
    key_list = ["{}_{}".format(order_list_cache_key, str(order_id).zfill(12)) for order_id in order_ids]
    cache_expire_list.apply_async(
        (key_list,),
        countdown=5,
        retry=True, retry_policy={
            'max_retries': 10,
            'interval_start': 0,
            'interval_step': 0.2,
            'interval_max': 0.2,
        }
    )


def get_delayed_orders(queryset):
    time_slot_str = str(get_order_ending_time())
    time_slot = datetime.datetime.strptime(time_slot_str, '%H:%M:%S').time()
    day_end = datetime.datetime.strptime("23:59:59", '%H:%M:%S').time()
    queryset = queryset.annotate(
        _tentative_delivery_date=Case(
            When(
                purchase_date__time__gt=time_slot,
                purchase_date__time__lte=day_end,
                is_queueing_order=True,
                then=F('purchase_date') + datetime.timedelta(days=2, hours=6)),
            When(
                purchase_date__time__gt=time_slot,
                purchase_date__time__lte=day_end,
                is_queueing_order=False,
                then=F('purchase_date') + datetime.timedelta(days=1, hours=6)),
            When(
                purchase_date__time__lte=time_slot,
                is_queueing_order=True,
                then=F('purchase_date') + datetime.timedelta(days=1, hours=6)),
            When(
                purchase_date__time__lte=time_slot,
                is_queueing_order=False,
                then=F('purchase_date__date') + datetime.timedelta(hours=6)),

            output_field=DateField()
        )
    ).filter(
        tentative_delivery_date__gt=F('_tentative_delivery_date')
    )
    return queryset


product_sorting_options = [
    {
        "name": "name_a_to_z",
        "value": "product__full_name",
        "value_es": "product.full_name.raw",
    },
    {
        "name": "name_z_to_a",
        "value": "-product__full_name",
        "value_es": "-product.full_name.raw",
    },
    {
        "name": "discount_low_to_high",
        "value": "product__discount_rate",
        "value_es": "product.discount_rate",
    },
    {
        "name": "discount_high_to_low",
        "value": "-product__discount_rate",
        "value_es": "-product.discount_rate",
    },
    {
        "name": "mrp_low_to_high",
        "value": "product__trading_price",
        "value_es": "product.trading_price",
    },
    {
        "name": "mrp_high_to_low",
        "value": "-product__trading_price",
        "value_es": "-product.trading_price",
    },
    {
        "name": "price_low_to_high",
        "value": "product_discounted_price",
        "value_es": "product.product_discounted_price",
    },
    {
        "name": "price_high_to_low",
        "value": "-product_discounted_price",
        "value_es": "-product.product_discounted_price",
    },
    {
        "name": "company_a_to_z",
        "value": "product__manufacturing_company__name",
        "value_es": "product.manufacturing_company.name.raw",
    },
    {
        "name": "company_z_to_a",
        "value": "-product__manufacturing_company__name",
        "value_es": "-product.manufacturing_company.name.raw",
    },
    {
        "name": "generic_a_to_z",
        "value": "product__generic__name",
        "value_es": "product.generic.name.raw",
    },
    {
        "name": "generic_z_to_a",
        "value": "-product__generic__name",
        "value_es": "-product.generic.name.raw",
    },
]


def get_sorting_options():
    # return all the names from product_sorting_options list

    return [option["name"] for option in product_sorting_options]


def get_sorting_value(name, is_es_sorting = False):
    # return value from product_sorting_options list for given name
    if is_es_sorting:
        return next((x.get("value_es") for x in filter(lambda x: x["name"] == name, product_sorting_options)), [])
    return next((x.get("value") for x in filter(lambda x: x["name"] == name, product_sorting_options)))


def get_organization_order_closing_and_reopening_time(ignore_if_invalid = True):
    from common.cache_keys import ORGANIZATION_SETTINGS_CACHE_KEY_PREFIX
    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    try:
        org_setting_cache_key = f"{ORGANIZATION_SETTINGS_CACHE_KEY_PREFIX}{distributor_id}"
        org_setting_cache = cache.get(org_setting_cache_key)
        if org_setting_cache:
            setting = org_setting_cache
        else:
            setting = Organization.objects.only('pk').get(pk=distributor_id).get_settings()
        order_re_opening_date = convert_utc_to_local(setting.order_re_opening_date)
        order_closing_date = convert_utc_to_local(setting.order_stopping_date)
        if ((order_closing_date.strftime("%Y%m%d-%H%M%S") > datetime.datetime.now().strftime("%Y%m%d-%H%M%S")) or (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") > order_re_opening_date.strftime("%Y%m%d-%H%M%S"))) and ignore_if_invalid:
            return None, None

        return order_closing_date, order_re_opening_date
    except:
        return None, None

def get_delivery_date_for_product(is_queueing_item):
    # return the delivery date based on order closing / reopening /current date
    current_date_time = convert_utc_to_local(datetime.datetime.now())
    order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time()
    date_time_for_product_delivery_date = current_date_time
    if (order_closing_date and order_reopening_date) and current_date_time < order_reopening_date and current_date_time >= order_closing_date:
        date_time_for_product_delivery_date = order_reopening_date
    return get_tentative_delivery_date(
        date_time_for_product_delivery_date,
        is_queueing_item
    )

def get_order_closing_info():
    from common.cache_keys import ORGANIZATION_SETTINGS_CACHE_KEY_PREFIX
    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)

    org_setting_cache_key = f"{ORGANIZATION_SETTINGS_CACHE_KEY_PREFIX}{distributor_id}"
    org_setting_cache = cache.get(org_setting_cache_key)
    if org_setting_cache:
        setting = org_setting_cache
    else:
        setting = Organization.objects.only('pk').get(pk=distributor_id).get_settings()
    datetime_format = "%m, %B %Y %I:%M %p"
    order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time()
    is_order_disabled = True if (order_closing_date and order_reopening_date) else False
    if setting.order_stopping_message:
        message = setting.order_stopping_message
    elif (order_closing_date and order_reopening_date) and not setting.order_stopping_message:
        message = (
            f"Sorry, Order Service is Temporarily Disabled from {order_closing_date.strftime(datetime_format)}"
            f" to {order_reopening_date.strftime(datetime_format)}."
            f" Please try again after {order_reopening_date.strftime(datetime_format)}."
        )
    else:
        message = ""
    return is_order_disabled, message

def get_next_valid_delivery_date(delivery_date):
    delivery_date = get_date_obj_from_date_str(
        delivery_date,
        "%Y-%m-%d"
    )

    order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time(False)
    delivery_date_by_order_closing_date = get_tentative_delivery_date(order_closing_date)
    delivery_date_by_order_reopening_date = get_tentative_delivery_date(order_reopening_date)
    if not delivery_date_by_order_reopening_date or not delivery_date_by_order_closing_date:
        return delivery_date + datetime.timedelta(days=1)
    if delivery_date_by_order_reopening_date > delivery_date >= delivery_date_by_order_closing_date:
        return delivery_date_by_order_reopening_date
    return delivery_date + datetime.timedelta(days=1)


def calculate_product_price(trading_price, discount_rate):
    return trading_price - (trading_price * discount_rate / 100)


def calculate_total_quantity_based_on_various_criteria(
        product,
        item,
        user_id,
        orderable_stock=None,
        product_order_mode=None
):
    """
    Returns the total quantity for a product considering different delivery hubs.

    Parameters:
    - product (object): The product for which the total quantity is calculated.
    - item (dict): A dictionary containing item details, including 'total_quantity'.
    - User_id (int): The user's ID for fetching user-related information.

    Returns:
    - int: The total quantity based on the specified criteria, including order limits,
        minimum order quantity, and available stock for the given product.

    This function calculates the total quantity for a product based on various criteria
    such as minimum order quantity, available stock, and daily order limits.
    The result takes into account the user's delivery hub to apply hub-specific limits.
    """
    total_qty = item.get('total_quantity', 0)
    change = item.get("change", 0)
    is_decrement = change < 0

    try:
        user_delivery_hub_short_code = get_user_profile_details_from_cache(
            user_id=user_id
        ).organization.delivery_hub.short_code

        if product_order_mode != AllowOrderFrom.OPEN:

            # follow these below conditions,
            # if product.minimum_order_quantity is more than 1
            if product.minimum_order_quantity > 1:
                # Check if order quantity is greater than 1 and
                # less then minimum order quantity
                # then assign 0
                # Assume orderable stock is 3, moq 5 and order mode pre order in that case it should allow
                # Adding qty greater than 1 and less than min qty otherwise remove the item
                if (
                    1 < total_qty < product.minimum_order_quantity and
                    (
                        (
                            product_order_mode != AllowOrderFrom.STOCK_AND_NEXT_DAY and
                            total_qty > orderable_stock < product.minimum_order_quantity
                        ) or
                        (
                            product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
                            total_qty < orderable_stock
                        ) or
                        (
                            product_order_mode == AllowOrderFrom.STOCK and
                            total_qty < orderable_stock
                        )
                    ) and is_decrement
                    ):
                    total_qty = 0

                # Check if order quantity is not 0 and equal 1
                # then assign minimum_order_quantity in total_qty
                elif 0 != total_qty < product.minimum_order_quantity:
                    total_qty = product.minimum_order_quantity

            # Check order quantity not more than product stock
            if orderable_stock and total_qty > orderable_stock and orderable_stock > 0 and not is_decrement:
                total_qty = orderable_stock
        # If order mode is open allow any qty to add
        elif product_order_mode == AllowOrderFrom.OPEN and product.minimum_order_quantity > 1:
            # If qty is greater than one and smaller than MoQ
            if 1 < total_qty < product.minimum_order_quantity and is_decrement:
                total_qty = 0
            # Check if order quantity is not 0 and equal 1
            # then assign minimum_order_quantity in total_qty
            elif 0 != total_qty < product.minimum_order_quantity:
                total_qty = product.minimum_order_quantity


        # Check the daily order limit based on the user's delivery hub
        if user_delivery_hub_short_code == "MH-1":
            if total_qty >= product.order_limit_per_day_mirpur:
                total_qty = product.order_limit_per_day_mirpur
        elif user_delivery_hub_short_code == "UH-1":
            if total_qty >= product.order_limit_per_day_uttara:
                total_qty = product.order_limit_per_day_uttara
        else:
            if total_qty >= product.order_limit_per_day:
                total_qty = product.order_limit_per_day

        return total_qty

    except AttributeError:

        if product_order_mode != AllowOrderFrom.OPEN:
            # Check if order quantity is greater than 1 and
            # less then minimum order quantity
            # then assign 0
            # Assume orderable stock is 3, moq 5 and order mode pre order in that case it should allow
            # Adding qty greater than 1 and less than min qty otherwise remove the item
            if (
                1 < total_qty < product.minimum_order_quantity and
                (
                    (
                        product_order_mode != AllowOrderFrom.STOCK_AND_NEXT_DAY and
                        total_qty > orderable_stock < product.minimum_order_quantity
                    ) or
                    (
                        product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
                        total_qty < orderable_stock
                    ) or
                    (
                        product_order_mode == AllowOrderFrom.STOCK and
                        total_qty < orderable_stock
                    )
                ) and is_decrement
                ):
                total_qty = 0

            # Check if order quantity is not 0 or equal 1
            # then assign minimum_order_quantity in total_qty
            elif 0 != total_qty < product.minimum_order_quantity:
                total_qty = product.minimum_order_quantity

            # Check order quantity not more than product stock
            if orderable_stock and total_qty > orderable_stock and orderable_stock > 0:
                total_qty = orderable_stock

        # If order mode is open allow any qty to add
        elif product_order_mode == AllowOrderFrom.OPEN and product.minimum_order_quantity > 1:
            # If qty is greater than one and smaller than MoQ
            if 1 < total_qty < product.minimum_order_quantity and is_decrement:
                total_qty = 0
            # Check if order quantity is not 0 and equal 1
            # then assign minimum_order_quantity in total_qty
            elif 0 != total_qty < product.minimum_order_quantity:
                total_qty = product.minimum_order_quantity

        # Check order limit
        if total_qty >= product.order_limit_per_day:
            total_qty = product.order_limit_per_day

        return total_qty

def remove_delivery_coupon(customer_organization_id, delivery_date):
    """Remove delivery coupon from order

    Args:
        customer_organization_id (int): organization if of the customer
        delivery_date (str(2023-10-25)): delivery date of the orders
    """
    from common.healthos_helpers import HealthOSHelper

    health_os_helper = HealthOSHelper()
    coupon_stock_id = health_os_helper.get_delivery_coupon_stock_id()
    delivery_coupon_price = health_os_helper.get_delivery_coupon_price()
    # Find the coupon io logs
    coupon_io_logs_qs = StockIOLog.objects.filter(
        status=Status.DISTRIBUTOR_ORDER,
        organization_id=customer_organization_id,
        stock_id=coupon_stock_id,
        purchase__tentative_delivery_date=delivery_date,
        purchase__distributor_order_type=DistributorOrderType.ORDER,
        purchase__purchase_type=PurchaseType.VENDOR_ORDER,
        purchase__current_order_status__in=[
            OrderTrackingStatus.PENDING,
            OrderTrackingStatus.ACCEPTED,
            OrderTrackingStatus.IN_QUEUE
        ],
        purchase__invoice_group__isnull=True
    )
    order_ids = []
    entry_by_id = None
    # Update order amount related data after removing coupon
    for item in coupon_io_logs_qs:
        item.status = Status.INACTIVE
        entry_by_id = item.entry_by_id
        StockIOLog.objects.bulk_update([item], ["status"])
        item.purchase.distributor_order_group.update_order_amount(order=True)
        order_ids.append(str(item.purchase_id))
    logger.info(
        f"Delivery coupon removed for Organization: {customer_organization_id}, Orders: {', '.join(order_ids)}"
    )
    notification_title = "Free Delivery!!!"
    notification_body = (
        f"Great! You have reached your minimum order amount for this delivery."
        f"The {delivery_coupon_price} BDT delivery cost from your previous order have been removed."
    )
    # Send push notification
    send_push_notification_to_mobile_app_by_org.delay(
        org_ids=[customer_organization_id],
        title=notification_title,
        body=notification_body,
        data={},
        entry_by_id=entry_by_id
    )


def calculate_queueing_quantity_based_on_various_criteria(
        item,
        _updated_qty,
        product,
        stock,
        product_order_mode
):
    """
        Calculate the pre-order quantity based on various criteria including user input,
        updated quantity, product details, and stock availability.

        Parameters:
        - item (dict): A dictionary containing information about the item, including the total_quantity.
        - _updated_qty (int): The updated quantity for the item.
        - product (object): An object representing the product, with attributes such as minimum_order_quantity.
        - stock (object): An object representing the stock availability, with attributes like orderable_stock.
        - product_order_mode (enum- int): Represent current order mode of a product

        Returns:
        int: The calculated pre-order quantity based on the specified conditions.
    """
    # get user given order quantity
    given_qty = item.get('total_quantity', 0)
    change = item.get("change", 0)
    is_decrement = change < 0
    # If orderable stock is less than MoQ it should only add regular item in cart at first request
    if (
        product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
        (0 < stock.orderable_stock <= _updated_qty or _updated_qty < stock.orderable_stock) and
        given_qty == 1
        ):
        return 0

    # get additional quantity which must be added in pre-order
    additional_qty = abs(given_qty - _updated_qty)

    # follow these below conditions,
    # if product.minimum_order_quantity is more than 1
    if product.minimum_order_quantity > 1:
        # if a user has regular quantity,
        # and additional_qty is more than 1 and less than product.minimum_order_quantity
        # then pre-order quantity should be 0
        if _updated_qty and 1 < additional_qty < product.minimum_order_quantity and is_decrement:
            queueing_qty = 0

        # if a user has regular quantity,
        # and additional_qty is not 0 and equal 1 and less than product.minimum_order_quantity
        # then pre-order quantity should be product.minimum_order_quantity
        elif (
            _updated_qty and
            0 != additional_qty < product.minimum_order_quantity
            ):
            queueing_qty = product.minimum_order_quantity

        # if a user has regular quantity,
        # and additional_qty is equal more than product.minimum_order_quantity,
        # then pre-order quantity should be additional_qty
        elif _updated_qty and additional_qty >= product.minimum_order_quantity:
            queueing_qty = additional_qty
        else:
            queueing_qty = 0
    else:
        queueing_qty = additional_qty

    # if product stock is 0,
    # then user given order quantity will be added in pre-order
    if stock.orderable_stock <= 0:

        # follow these below conditions,
        # if product.minimum_order_quantity is more than 1
        if product.minimum_order_quantity > 1:

            # if a user has regular quantity,
            # and additional_qty is more than 1 and less than product.minimum_order_quantity
            # then pre-order quantity should be 0
            if 1 < additional_qty < product.minimum_order_quantity and is_decrement:
                queueing_qty = 0

            # if a user has regular quantity,
            # and additional_qty is not 0 and equal 1 and less than product.minimum_order_quantity
            # then pre-order quantity should be product.minimum_order_quantity
            elif 0 != additional_qty < product.minimum_order_quantity:
                queueing_qty = product.minimum_order_quantity

            # if additional quantity is greater than product.minimum_order_quantity,
            # then queueing_qty should be value of additional quantity
            elif additional_qty >= product.minimum_order_quantity:
                queueing_qty = additional_qty
            else:
                queueing_qty = 0

        # if product.minimum_order_quantity is 1
        else:
            queueing_qty = additional_qty

    return queueing_qty


def remove_discount_factor_for_coupon(request, data):
    """
    Removes the discount factor for a given coupon from the cumulative discount factor.

    Args:
    - request: The HTTP request object.
    - data: Dictionary containing the coupon ID information.

    Returns:
    - float: Updated discount factor after removing the coupon's discount factor or
            0.00 if the coupon ID matches the provided data.

    Note:
    - This function fetches the cumulative discount factor for a customer based on the organization ID
    from the request. If the provided coupon ID matches the 'EXPRESS_DELIVERY_STOCK_ID' from the environment,
    it returns 0.00, effectively removing the discount factor for that coupon. Otherwise, it returns
    the original discount rate factor for the customer.
    """

    # Importing necessary modules here to avoid circular import error
    from common.healthos_helpers import CustomerHelper

    # Fetch the cumulative discount factor for the customer's organization
    discount_rate_factor = CustomerHelper(
        request.user.organization_id
    ).get_cumulative_discount_factor()
    # Get the coupon ID from environment variables
    coupon = os.environ.get("EXPRESS_DELIVERY_STOCK_ID", None)
    # Check if the provided data's ID matches the coupon ID
    if str(data["id"]) == coupon:
        return 0.00  # If the coupon matches, remove the discount factor by returning 0.00
    else:
        return discount_rate_factor  # Otherwise, return the original discount factor


def get_product_dynamic_discount_rate(user_org_id, trading_price, discount_rate, stock_id):
    """Will return the calculated dynamic discount rate for a product based on org and area discount

    Args:
        user_org_id (int): request user organization id
        trading_price (float): product MRP
        discount_rate (float): product discount rate
        stock_id (int): stock id

    Returns:
        decimal: _description_
    """
    from common.healthos_helpers import CustomerHelper
    from decimal import Decimal

    # Return if trading price is 0
    if not trading_price:
        return 0.00


    dynamic_discount_factor = CustomerHelper(
        organization_id=user_org_id
    ).get_organization_and_area_discount()

    product_mrp = Decimal(trading_price)
    base_discount = Decimal(discount_rate)


    org_discount_factor = dynamic_discount_factor.get("organization_discount_factor", 0.00)
    area_discount_factor = dynamic_discount_factor.get("area_discount_factor", 0.00)

    price = product_mrp - (base_discount * product_mrp) / 100
    price = price - (org_discount_factor * price) / 100
    price = price - (area_discount_factor * price) / 100
    final_discount_amount = product_mrp - price
    dynamic_discount_rate = round((final_discount_amount / product_mrp) * 100, 3)

    coupon = os.environ.get("EXPRESS_DELIVERY_STOCK_ID", None)
    # Check if the provided data's ID matches the coupon ID
    # If the coupon matches, remove the discount factor by returning 0.00
    if str(stock_id) == coupon:
        return 0.00
    else:
        return dynamic_discount_rate
