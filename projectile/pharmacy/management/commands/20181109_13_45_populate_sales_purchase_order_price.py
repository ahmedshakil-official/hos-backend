import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from pharmacy.models import (Stock, StockIOLog)
from common.enums import Status

logger = logging.getLogger(__name__)

def get_filtered_stock_io(filtered_argument):
    # this method return the last entry for given filter
    objects = StockIOLog.objects.filter(
        **filtered_argument).order_by('-id')[:1]
    if objects.exists():
        # if this queryset exists returing last entry by using -id and [0]
        return objects[0]
    # returning none
    return None

def get_rate(obj):
    # this method return rate of primary unit for given stock io log
    rate = 0
    # if object is not none
    if obj is not None:
        # if stock io was stored using secoendery unit
        if obj.secondary_unit_flag:
            rate = obj.rate / obj.conversion_factor
        else:
            # no need to convert as this stock io was stored using primary unit
            rate = obj.rate
    # if object is none
    return rate

def get_sales_price(stock):
    # find last sales record in Stock IO of given stock
    # note that last_obj can be none, if for this stock no sales
    # has been made
    last_obj = get_filtered_stock_io(
        {
            'stock': stock,
            'status': Status.ACTIVE,
            'sales__isnull': False,
            'rate__gt': 0
        }
    )
    return get_rate(last_obj)

def get_purchase_price(stock):
    # find last purchase record in Stock IO of given stock
    # note that last_obj can be none, if for this stock no purchase
    # has been made

    last_obj = get_filtered_stock_io(
        {
            'stock': stock,
            'status': Status.ACTIVE,
            'purchase__isnull': False,
            'rate__gt': 0
        }
    )
    return get_rate(last_obj)

def get_order_price(stock):
    # find last purchase order record in Stock IO of given stock
    # note that last_obj can be none, if for this stock no purchase order
    # has been made

    last_obj = get_filtered_stock_io(
        {
            'stock': stock,
            'status': Status.PURCHASE_ORDER,
            'purchase__isnull': False,
            'rate__gt': 0
        }
    )
    return get_rate(last_obj)

def populate_data():
    # fetch all those stock, what have enty on stock io
    stocks = Stock.objects.filter(
        # taking active store point into account
        store_point__status=Status.ACTIVE,
        # taking active product into account
        product__status=Status.ACTIVE,
        # this stock must have associated stock io
        # by this, excluding all those stock who have no entry on stock io
        stocks_io__isnull=False,
    ).only(
        'product__id',
        'store_point__id'
    ).select_related(
        'store_point',
        'product'
    ).distinct()

    for item in tqdm(stocks):
        # travarse through each item : Stock
        item.sales_rate = get_sales_price(item)
        item.purchase_rate = get_purchase_price(item)
        item.order_rate = get_order_price(item)
        item.save()


class Command(BaseCommand):
    '''
    This management script popluate last sales, purchase & order price of a product
    '''

    def handle(self, **options):
        populate_data()
