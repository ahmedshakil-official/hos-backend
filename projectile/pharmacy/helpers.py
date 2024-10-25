# -*- coding: utf-8 -*-

import logging
import time
import os
import pandas as pd
from pytz import timezone
from datetime import datetime

from django.db.models import (
    signals,
    Case,
    F,
    When,
    Sum,
)
from django.conf import settings

from .signals import (
    pre_save_stock_io_log,
    post_delete_stock_io_log,
    post_save_product,
    pre_save_stock,
)

from common.enums import Status
from common.helpers import custom_elastic_rebuild
from core.enums import PriceType, PersonGroupType
from pharmacy.models import Product, Stock, StockIOLog, Sales, Purchase, PurchaseRequisition
from pharmacy.enums import (
    SalesType,
    StockIOType,
    OrderTrackingStatus,
    DistributorOrderType,
    PurchaseType,
    PurchaseOrderStatus,
)


logger = logging.getLogger(__name__)


def stop_product_signal():
    signals.post_save.disconnect(post_save_product, sender=Product)

def stop_stock_signal():
    signals.pre_save.disconnect(pre_save_stock, sender=Stock)

def stop_stock_io_signal():
    signals.pre_save.disconnect(pre_save_stock_io_log, sender=StockIOLog)
    signals.post_delete.disconnect(post_delete_stock_io_log, sender=StockIOLog)

def stop_inventory_signal():
    stop_product_signal()
    stop_stock_signal()
    stop_stock_io_signal()

def start_product_signal():
    signals.post_save.connect(post_save_product, sender=Product)

def start_stock_signal():
    signals.pre_save.connect(pre_save_stock, sender=Stock)

def start_stock_io_signal():
    signals.pre_save.connect(pre_save_stock_io_log, sender=StockIOLog)
    signals.post_delete.connect(post_delete_stock_io_log, sender=StockIOLog)

def start_inventory_signal():
    start_product_signal()
    start_stock_signal()
    start_stock_io_signal()

def add_log_price_on_stock_queryset(queryset, is_sale=True):
    '''
    This method take a queryset and is_sale(True for sales, Flase for purchase) of
    pharmacy.model.stock and caclulate log price accrodingly
    Parameters
    ----------
    queryset: Django queryset
        A django queryset of stlock model
    Raises
    ------
    No error is raised by this method
    Returns
    -------
    queryset: Django queryset
        A django queryset of stlock model with log price
    '''
    # for purhcase(is_sale=False)
    if not is_sale:
        return queryset.annotate(
            log_price=Case(
                When(
                    organization__organizationsetting__purchase_price_type=PriceType.PRODUCT_PRICE,
                    then=F('product__purchase_price')
                ),
                When(
                    organization__organizationsetting__purchase_price_type=\
                        PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                    purchase_rate__lte=0,
                    then=F('product__purchase_price')
                ),
                When(
                    organization__organizationsetting__purchase_price_type=\
                        PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                    product__purchase_price__gt=0,
                    then=F('product__purchase_price')
                ),
                default=F('purchase_rate'),
            )
        )

    # for sales(is_sale=True)
    return queryset.annotate(
        log_price=Case(
            When(
                organization__organizationsetting__price_type=PriceType.PRODUCT_PRICE,
                then=F('product__trading_price')
            ),
            When(
                organization__organizationsetting__price_type=\
                    PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                sales_rate__lte=0,
                then=F('product__trading_price')
            ),
            When(
                organization__organizationsetting__price_type=\
                    PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                product__trading_price__gt=0,
                then=F('product__trading_price')
            ),
            default=F('sales_rate'),
        )
    )


def add_sales_purchase_log_price(queryset):
    """[summary]
    Arguments:
        queryset {[queryset object]} -- [queryset of stock model]
    """
    return queryset.annotate(
        purchase_log_price=Case(
            When(
                organization__organizationsetting__purchase_price_type=PriceType.PRODUCT_PRICE,
                then=F('product__purchase_price')
            ),
            When(
                organization__organizationsetting__purchase_price_type=\
                    PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                purchase_rate__lte=0,
                then=F('product__purchase_price')
            ),
            When(
                organization__organizationsetting__purchase_price_type=\
                    PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                product__purchase_price__gt=0,
                then=F('product__purchase_price')
            ),
            default=F('purchase_rate'),
        ),
        sales_log_price=Case(
            When(
                organization__organizationsetting__price_type=PriceType.PRODUCT_PRICE,
                then=F('product__trading_price')
            ),
            When(
                organization__organizationsetting__price_type=\
                    PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                sales_rate__lte=0,
                then=F('product__trading_price')
            ),
            When(
                organization__organizationsetting__price_type=\
                    PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                product__trading_price__gt=0,
                then=F('product__trading_price')
            ),
            default=F('sales_rate'),
        )
    )


# Get list of pk of published products company cached
def get_cached_company_ids_of_published_products(self):
    from django.core.cache import cache
    from common.utils import get_global_based_discarded_list
    from core.models import Organization
    from pharmacy.models import ProductManufacturingCompany

    cache_key = 'manufacturing_company_published'
    published_company_ids = cache.get(cache_key)
    if published_company_ids is None:
        organization = Organization.objects.only('id').get(
            pk=os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        )
        discarded_lists = get_global_based_discarded_list(
            self, ProductManufacturingCompany, organization)
        published_company = ProductManufacturingCompany().get_all_from_organization(
            organization,
            Status.ACTIVE,
        ).values_list('pk', flat=True).exclude(pk__in=discarded_lists).filter(
            product_manufacturing_company__status=Status.ACTIVE,
            product_manufacturing_company__is_published=True,
            product_manufacturing_company__is_salesable=True,
            product_manufacturing_company__order_limit_per_day__gt=0,
        ).distinct()
        published_company_list = list(published_company)
        timeout = 604800 # 7 days (7*24*60*60)
        cache.set(cache_key, published_company_list, timeout)
        return published_company_list
    return published_company_ids


def get_product_short_name(product):
    name = product.name
    form = product.form.name if product.form_id else None
    strength = product.strength
    if form and strength:
        return f"{form} {name} {strength}"
    elif form and not strength:
        return f"{form} {name}"
    elif strength and not form:
        return f"{name} {strength}"
    else:
        return f"{name}"


def get_average_purchase_price(stock_id, end_datetime=None, person_organization_supplier_alias=None):

    ORGANIZATION_ID = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    date = datetime.now(
        timezone('Asia/Dhaka')
    )
    query_set = StockIOLog.objects.filter(
        organization__id=ORGANIZATION_ID,
        stock__id=stock_id,
        status=Status.ACTIVE,
        purchase__current_order_status=OrderTrackingStatus.PENDING,
        purchase__distributor_order_type=DistributorOrderType.CART,
        purchase__is_sales_return=False,
        purchase__purchase_order_status=PurchaseOrderStatus.DEFAULT,
        purchase__purchase_type=PurchaseType.PURCHASE,
        purchase__status=Status.ACTIVE,
    )

    if end_datetime:
        query_set = query_set.filter(
            purchase__purchase_date__lte=end_datetime
        )

    if person_organization_supplier_alias is not None:
        query_set = query_set.filter(
            purchase__person_organization_supplier__alias=person_organization_supplier_alias
        )


    query_set = query_set.values(
        'date',
    ).annotate(
        qty=Sum('quantity'),
        cost=Sum(
            F('quantity') *
            F('rate'),
        ),
    ).order_by(
        '-date',
        'qty',
        'cost'
    )[0:3]

    data = pd.DataFrame.from_records(
        list(query_set)
    )

    try:
        if data['qty'].sum() > 0:
            return data['cost'].sum() / data['qty'].sum()
    except:
        return 0
    return 0


def create_requisition_for_procure(
    _datetime_now,
    procure,
    procure_items,
    organization_id,
    user,
    store_point_id,
    department_id,):
    data = {
        "requisition_date": _datetime_now.date(),
        "purchase_date": _datetime_now,
        "status": Status.DRAFT,
        "person_organization_receiver": user.get_person_organization_for_employee(only_fields=['id']),
        "person_organization_supplier_id": procure.supplier_id,
        "receiver_id": procure.employee.person_id,
        "supplier_id": procure.supplier.person_id,
        "store_point_id": store_point_id,
        "department_id": department_id,
        "entry_by_id": user.id,
        "organization_id": organization_id,
        "vouchar_no": procure.invoices,
        "remarks": procure.invoices,
    }

    requisition_instance = Purchase.objects.create(**data)
    # custom_elastic_rebuild('pharmacy.models.Purchase', {'id': requisition_instance.id})

    for item in procure_items:
        io_item = {
            "date": _datetime_now.date(),
            "status": Status.DRAFT,
            "stock_id": item.get('stock'),
            "quantity": float(item.get('quantity')),
            "batch": "N/A",
            "primary_unit_id": item.get('stock__product__primary_unit'),
            "secondary_unit_id": item.get('stock__product__secondary_unit'),
            "conversion_factor": item.get('stock__product__conversion_factor'),
            "secondary_unit_flag": False,
            "type": StockIOType.INPUT,
            "entry_by_id": user.id,
            "organization_id": organization_id,
            "purchase": requisition_instance,
        }
        StockIOLog.objects.create(**io_item)
    return requisition_instance


def create_purchase_or_order_for_procure(
    _datetime_now,
    procure,
    procure_items,
    organization_id,
    user,
    store_point_id,
    reference_id,
    status):
    total_amount = sum(item.get('rate') * item.get('quantity') for item in procure_items)
    data = {
        "amount": float(total_amount),
        "purchase_date": _datetime_now,
        "status": status,
        "person_organization_receiver": user.get_person_organization_for_employee(only_fields=['id']),
        "person_organization_supplier_id": procure.supplier_id,
        "receiver_id": procure.employee.person_id,
        "supplier_id": procure.supplier.person_id,
        "purchase_order_status": PurchaseOrderStatus.COMPLETED,
        "store_point_id": store_point_id,
        "entry_by_id": user.id,
        "organization_id": organization_id,
        "vouchar_no": procure.invoices,
    }
    if status == Status.ACTIVE:
        data["copied_from_id"] = reference_id
        data["purchase_order_status"] = PurchaseOrderStatus.DEFAULT

    purchase_instance = Purchase.objects.create(**data)
    if status == Status.PURCHASE_ORDER:
        PurchaseRequisition.objects.create(
            purchase=purchase_instance,
            requisition_id=reference_id,
            organization_id=organization_id,
        )
    # custom_elastic_rebuild('pharmacy.models.Purchase', {'id': purchase_instance.id})

    for item in procure_items:
        io_item = {
            "date": _datetime_now.date(),
            "status": status,
            "stock_id": item.get('stock'),
            "quantity": float(item.get('quantity')),
            "rate": float(item.get('rate')),
            "batch": "N/A",
            "primary_unit_id": item.get('stock__product__primary_unit'),
            "secondary_unit_id": item.get('stock__product__secondary_unit'),
            "conversion_factor": item.get('stock__product__conversion_factor'),
            "secondary_unit_flag": False,
            "type": StockIOType.INPUT,
            "entry_by_id": user.id,
            "organization_id": organization_id,
            "purchase": purchase_instance,
        }
        StockIOLog.objects.create(**io_item)
    return purchase_instance


def is_order_exists_on_delivery_date(organization_id, delivery_date):
    """check if an organization have order on specific delivery date

    Args:
        organization_id (int): id of an organization
        delivery_date (_type_): delivery date (2023-12-20)
    """
    filters = {
        "status": Status.DISTRIBUTOR_ORDER,
        "distributor_order_type": DistributorOrderType.ORDER,
        "purchase_type": PurchaseType.VENDOR_ORDER,
        "organization_id": organization_id,
        "tentative_delivery_date": delivery_date
    }
    orders = Purchase.objects.filter(
        **filters
    ).exclude(
        current_order_status__in=[
            OrderTrackingStatus.CANCELLED,
            OrderTrackingStatus.REJECTED
        ]
    ).only("id")
    return orders.exists()
