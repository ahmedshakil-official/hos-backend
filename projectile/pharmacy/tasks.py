# -*- coding: ascii -*-
from __future__ import absolute_import, unicode_literals

import logging, os
import time
import math
from datetime import date
import pandas as pd
from dotmap import DotMap
from validator_collection import checkers

from django.db.models import (
    F,
    Q,
    Case,
    When,
    Sum,
    Prefetch,
)
from django.db.models.functions import Coalesce
from django.core.cache import cache

from projectile.celery import app

from common.enums import Status
from common.cache_keys import (
    PERSON_ORG_SUPPLIER_STOCK_RATE_AVG,
    STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX,
)
from common.helpers import send_log_alert_to_slack_or_mattermost
from common.utils import Round
from search.tasks import update_stock_document_lazy
from search.utils import update_stock_es_doc

from .models import StockIOLog, Stock, StorePoint, Product, Purchase
from .enums import StockIOType, PurchaseType, OrderTrackingStatus, DistributorOrderType
from .utils import get_is_queueing_item_value, remove_delivery_coupon
from .helpers import get_average_purchase_price

logger = logging.getLogger(__name__)


@app.task
def update_stock_related_data_for_purchase_lazy(purchase_pk):
    time.sleep(1)
    try:
        ios = StockIOLog.objects.filter(purchase__id=purchase_pk).only('stock')
        for io_item in ios:
            io_item.stock.update_avg_purchase_rate()
        logger.info("Successfully updated stocks for purchase of ID {}".format(purchase_pk))
    except Exception as exception:
        logger.info(
            "Unable to update stocks for purchase of ID {}, Exception: {}".format(
                purchase_pk, str(exception)
            )
        )

@app.task
def update_count_in_stock_lazy(stock_id, increase=False, decrease=False):
    # organizationwise_count io_log count update
    time.sleep(1)
    try:
        stock_by_id = Stock.objects.only(
            'id',
            'product__id',
            'organization',
        ).get(pk=stock_id)
        organization_wise = Stock.objects.filter(
            product__id=stock_by_id.product_id,
            organization__id=stock_by_id.organization_id
        )

        # global_count io_log count update
        # global_wise = stock.objects.filter(
        #     product=instance.stock.product_id,
        # )

        if increase:
            organization_wise.update(
                organizationwise_count=F('organizationwise_count') + 1
            )
            # global_wise.update(
            #     global_count=F('global_count') + 1
            # )
        if decrease:
            organization_wise.update(
                organizationwise_count=F('organizationwise_count') - 1
            )
            # global_wise.update(
            #     global_count=F('global_count') - 1
            # )
        logger.info("Successfully updated stocks count for Stock of ID {}".format(stock_id))
    except Exception as exception:
        logger.info(
            "Unable to update stocks count for Stock of ID {}, Exception: {}".format(
                stock_id, str(exception)
            )
        )


@app.task
def check_and_fix_current_stock_lazy(stock_id):
    # check and fix mismatched stock
    time.sleep(1)
    try:
        io_query_in = (
            (Q(stocks_io__purchase__isnull=True)
            | Q(stocks_io__purchase__purchase_type=PurchaseType.PURCHASE))
            & Q(stocks_io__status=Status.ACTIVE)
            & Q(stocks_io__type=StockIOType.INPUT)
        )

        io_query_out = (
            (Q(stocks_io__purchase__isnull=True)
            | Q(stocks_io__purchase__purchase_type=PurchaseType.PURCHASE))
            & Q(stocks_io__status=Status.ACTIVE)
            & Q(stocks_io__type=StockIOType.OUT)
        )
        queryset = Stock.objects.filter(
            pk=stock_id,
        ).only(
            'id',
            'stock'
        ).order_by()

        current_stock = queryset.prefetch_related('stocks_io').aggregate(
            current_stock=Coalesce(Sum(Case(When(
                io_query_in, then=F('stocks_io__quantity')))), 0.00) -
            Coalesce(Sum(Case(When(
                io_query_out, then=F('stocks_io__quantity')))), 0.00),
        ).get('current_stock')
        stock_instance = queryset.first()

        if stock_instance.stock != current_stock:
            queryset.update(stock=current_stock)
            stock_instance.expire_cache()
            logger.info("Successfully updated mismatched stock for Stock of ID {}".format(stock_id))
        else:
            logger.info("No update as stock is correct for Stock of ID {}".format(stock_id))
    except Exception as exception:
        logger.error(
            "Unable to update stock for Stock of ID {}, Exception: {}".format(
                stock_id, str(exception)
            )
        )


@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def adjust_stock_from_file_ecommerce(file_name, file_instance_pk, lower_limit, upper_limit, store_point_pk):
    from common.helpers import is_allowed_to_update_queueing_item_value
    from core.models import ScriptFileStorage
    from .helpers import stop_inventory_signal, start_inventory_signal

    time.sleep(1)
    stop_inventory_signal()
    try:
        stock_file = ScriptFileStorage.objects.get(pk=file_instance_pk)
        stock_df =  pd.read_csv(stock_file.content)
        data_df = stock_df[lower_limit:upper_limit]
        store_point = StorePoint.objects.get(pk=store_point_pk)
        base_stock_adjustment = store_point.get_base_stock_adjustment()
        distributor_settings = store_point.organization.get_settings()

        for index, item in data_df.iterrows():
            requesting_stock_qty = item['STOCK']
            stock_id = item['ID']

            if not math.isnan(requesting_stock_qty) and not math.isnan(stock_id):

                stock = Stock.objects.only(
                    'id',
                    'stock',
                    'orderable_stock'
                ).get(pk=stock_id)
                calculated_stock = stock.get_calculated_stock_for_ecommerce()

                adjustable_stock = 0

                if calculated_stock > requesting_stock_qty:
                    adjustable_stock = calculated_stock - requesting_stock_qty
                    io_type = StockIOType.OUT
                elif calculated_stock < requesting_stock_qty:
                    adjustable_stock = requesting_stock_qty - calculated_stock
                    io_type = StockIOType.INPUT

                if adjustable_stock > 0:
                    payload = {
                        'stock_id': stock_id,
                        'quantity': adjustable_stock,
                        'batch': 'N/A',
                        'date': date.today(),
                        'type': io_type,
                        'adjustment': base_stock_adjustment,
                        'primary_unit_id': stock.product.primary_unit_id,
                        'secondary_unit_id': stock.product.secondary_unit_id,
                        'organization_id': stock.organization_id
                    }
                    adjustment_io = StockIOLog.objects.create(**payload)
                    adjustment_io.save()
                if stock.stock != requesting_stock_qty:
                    stock.stock = requesting_stock_qty
                    stock.orderable_stock = stock.get_current_orderable_stock(requesting_stock_qty)
                    stock.save(update_fields=['stock', 'orderable_stock'])
                    stock.refresh_from_db()
                # Update product queueing status
                if stock.orderable_stock <= 0 and is_allowed_to_update_queueing_item_value(distributor_settings, stock.product):
                    Product.objects.filter(
                        pk=stock.product_id,
                        is_queueing_item=False
                    ).update(is_queueing_item=True)
                else:
                    Product.objects.filter(
                        pk=stock.product_id,
                        is_queueing_item=True
                    ).update(is_queueing_item=False)
                stock.expire_cache()
        logger.info(f"Successfully populated stock for file {file_name}")
    except Exception as exception:
        logger.info(
            f"Unable to populate stocks for file {file_name}, Exception: {str(exception)}"
        )

    start_inventory_signal()

@app.task(bind=True, max_retries=10)
def update_product_queueing_item_value(self, stock_id_list, settings):
    try:
        stock_instances = []
        product_instances = []
        stock_cache_key_list = []

        stocks = Stock.objects.filter(
            pk__in=stock_id_list
        ).only('id', 'ecom_stock', 'orderable_stock',)
        for stock in stocks:
            current_orderable_stock = stock.current_orderable_stock
            if stock.orderable_stock != current_orderable_stock:
                stock.orderable_stock = current_orderable_stock
                stock_instances.append(stock)
                logger.info(
                    f"Updated orderable stock for stock {stock.id}."
                )
            # Check if product is_queueing_item should change or not
            product = Product.objects.only('order_mode', 'is_queueing_item').get(pk=stock.product_id)
            is_queueing_item_value = get_is_queueing_item_value(
                stock.orderable_stock,
                product.order_mode,
                DotMap(settings)
            )
            if is_queueing_item_value != product.is_queueing_item:
                product.is_queueing_item = is_queueing_item_value
                product_instances.append(product)
                logger.info(
                    f"Set product is queueing item to {is_queueing_item_value} for stock {stock.id}."
                )
            stock_key_list = [
                # f"stock_instance_{str(stock).zfill(12)}",
                f"{STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX}_{str(stock.id).zfill(12)}"
            ]
            stock_cache_key_list.extend(stock_key_list)
        Stock.objects.bulk_update(stock_instances, ['orderable_stock',], batch_size=500)
        Product.objects.bulk_update(product_instances, ['is_queueing_item',], batch_size=500)
        # Expire stock cache
        cache.delete_many(stock_cache_key_list)
        filters = {"pk__in": stock_id_list}
        update_stock_es_doc(queryset=stocks)
        # update_stock_document_lazy.apply_async(
        #     (
        #         filters,
        #     ),
        #     countdown=1,
        #     retry=True, retry_policy={
        #         'max_retries': 10,
        #         'interval_start': 0,
        #         'interval_step': 0.2,
        #         'interval_max': 0.2,
        #     }
        # )
    except Exception as exc:
        logger.info('will retry in 5 sec')
        self.retry(exc=exc, countdown=5)

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def set_ecom_stock_from_file_lazy(file_name, file_instance_pk, lower_limit, upper_limit):
    from core.models import ScriptFileStorage
    from .helpers import stop_inventory_signal, start_inventory_signal

    stop_inventory_signal()
    try:
        stock_file = ScriptFileStorage.objects.only('content').get(pk=file_instance_pk)
        stock_df =  pd.read_csv(stock_file.content)
        data_df = stock_df[lower_limit:upper_limit]

        for index, item in data_df.iterrows():
            requesting_stock_qty = item.get('STOCK', '')
            stock_id = item.get('ID', '')

            try:
                if stock_id and requesting_stock_qty:
                    requesting_stock_qty = int(float(requesting_stock_qty))
                    stock_id = int(float(stock_id))
                if not math.isnan(requesting_stock_qty) and not math.isnan(stock_id):
                    stock = Stock.objects.only(
                        'id',
                        'stock',
                        'orderable_stock'
                    ).get(pk=stock_id)
                    current_orderable_stock = stock.get_current_orderable_stock(requesting_stock_qty)
                    if stock.ecom_stock != requesting_stock_qty or stock.orderable_stock != current_orderable_stock:
                        logger.info(
                            "{} PREV QTY : {} CURRENT QTY : {}".format(
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
            except  Exception as exception:
                logger.info(
                    f"Unable to populate stocks for stock {stock_id}, Exception: {str(exception)}"
                )

        logger.info(f"Successfully populated stock for file {file_name}")
        stock_id_list = data_df.ID.values.tolist()
        stock_id_list = filter(checkers.is_numeric, stock_id_list)
        filters = {"pk__in": list(stock_id_list)}
        update_stock_document_lazy.apply_async(
            (
                filters,
            ),
            countdown=1,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
    except Exception as exception:
        logger.info(
            f"Unable to populate stocks for file {file_name}, Exception: {str(exception)}"
        )

    start_inventory_signal()

@app.task
def calculate_profit_by_order_id_lazy(order_id):
    from common.helpers import custom_elastic_rebuild
    from .profit_helpers import get_profit_by_order
    get_profit_by_order(order_id)
    order_key_list = [
        'purchase_distributor_order_{}'.format(str(order_id).zfill(12)),
    ]
    cache.delete_many(order_key_list)
    custom_elastic_rebuild(
        'pharmacy.models.Purchase', {'id': order_id}
    )

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def apply_additional_discount_on_order(
    order_id,
    group_grand_total,
    order_grand_total,
    is_queueing_order_value,
    is_invoice_group_null=True):
    from .utils import get_additional_discount_data

    try:
        order_instance = Purchase.objects.only(
            'purchase_date',
            'organization__offer_rules',
            'organization',
            'tentative_delivery_date',
            'is_queueing_order'
        ).get(pk=order_id)
        # get total orders and total amount of orders
        order_instances = Purchase.objects.filter(
            organization=order_instance.organization,
            tentative_delivery_date=order_instance.tentative_delivery_date,
            # is_queueing_order=order_instance.is_queueing_order,
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
            current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.IN_QUEUE
            ],
            invoice_group__isnull=is_invoice_group_null
        )
        order_grand_total = order_instances.aggregate(
            amount_total=Coalesce(Round(Sum('amount') - Sum('discount') + Sum('round_discount')), 0.00)
        ).get('amount_total', 0)
        additional_discount_data = get_additional_discount_data(
            order_grand_total,
            is_queueing_order_value,
            order_instance,
        )

        for order in order_instances:
            if additional_discount_data.get('discount', 0) > 0:
                order.apply_additional_discount(
                    **additional_discount_data
                )
    except:
        pass

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_ecommerce_stock_on_order_or_order_status_change_lazy(order_id):
    try:
        order = Purchase.objects.only(
            'id',
            'current_order_status',
            'entry_by_id',
            'alias',
            'tentative_delivery_date',
            'distributor_order_group_id',
            'is_queueing_order',
            'updated_by_id',
            'organization_id',
            'system_platform',
        ).get(pk=order_id)
        order.update_ecommerce_stock_on_order_or_order_status_change()
    except:
        pass

@app.task
def populate_stock_supplier_avg_rate_cache(stock_id):
    from core.models import Organization

    base_cache_key = PERSON_ORG_SUPPLIER_STOCK_RATE_AVG
    org_id =  os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    org = Organization.objects.only('id').get(pk=org_id)
    supplier_alias_list = org.get_po_supplier_alias_list()
    timeout = 43200
    for supplier_alias in supplier_alias_list:
        supplier_avg_rate = get_average_purchase_price(
            stock_id=stock_id,
            person_organization_supplier_alias=supplier_alias
        )
        cache_key = f"{base_cache_key}_{stock_id}_{supplier_alias}"
        cache.set(cache_key, supplier_avg_rate, timeout)

@app.task
def fix_stock_on_mismatch_and_send_log_to_mm(stock_id):
    """Compare current stock with calculated stock and fix if needed

    Args:
        stock_id (_type_): ok of stock instance
    """
    try:
        stock_instance = Stock.objects.only('ecom_stock').get(pk=stock_id)
        current_stock = stock_instance.ecom_stock
        calculated_stock = stock_instance.get_calculated_stock_for_ecommerce()
        if current_stock != calculated_stock:
            stock_instance.ecom_stock = calculated_stock
            stock_instance.save(
                update_fields=['ecom_stock', 'orderable_stock']
            )
            message = f"Fix stock for {stock_id}, Prev stock: {current_stock}, Calculated Stock: {calculated_stock}"
            send_log_alert_to_slack_or_mattermost(message)
    except:
        pass


@app.task
def remind_orgs_on_product_re_stock(stock_id, product_name, product_price):
    from .models import StockReminder
    from expo_notification.utils import send_push_notification_to_mobile_app_by_org_ids
    stock_reminders = StockReminder.objects.filter(
        stock_id=stock_id,
        status=Status.ACTIVE,
        reminder_count=0,
    )
    if stock_reminders.exists():
        # Send push notification to users, who didn't set a preferable price
        org_without_suggested_price = stock_reminders.filter(
            preferable_price__isnull=True,
        )
        org_ids_without_suggested_price = list(
            org_without_suggested_price.values_list('organization_id', flat=True)
        )
        if org_ids_without_suggested_price:
            send_push_notification_to_mobile_app_by_org_ids(
                org_ids_without_suggested_price,
                "Restock Alert !!!",
                "The Product {} is available again, order before stock out.".format(product_name),
            )
            org_without_suggested_price.update(
                reminder_count=F('reminder_count') + 1,
            )
        # Send push notification to users, who set a preferable price
        org_with_suggested_price = stock_reminders.filter(
            preferable_price__isnull=False,
            preferable_price__gte=product_price,
        )
        org_ids_with_suggested_price = list(
            org_with_suggested_price.values_list('organization_id', flat=True)
        )
        if org_ids_with_suggested_price:
            send_push_notification_to_mobile_app_by_org_ids(
                org_ids_with_suggested_price,
                "Restock Alert !!!",
                "The Product {} is available again with a lower rate, order before stock out.".format(product_name),
            )
            org_with_suggested_price.update(
                reminder_count=F('reminder_count') + 1,
            )

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def remove_delivery_coupon_lazy(customer_organization_id, delivery_date):
    remove_delivery_coupon(
        customer_organization_id=customer_organization_id,
        delivery_date=delivery_date
    )
