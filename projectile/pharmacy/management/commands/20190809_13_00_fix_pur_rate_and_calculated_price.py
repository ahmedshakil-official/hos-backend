import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.helpers import (
    get_organization_by_input_id,
    get_storepoint_by_id,
)

from common.enums import Status
from common.utils import get_ratio

from pharmacy.models import (
    Stock,
    StockIOLog
)

from pharmacy.helpers import (
    start_stock_signal,
    stop_stock_signal
)
from pharmacy.enums import PurchaseType


logger = logging.getLogger(__name__)


def get_filtered_stock_io(filtered_argument):
    # this method will return the last entry of IOLog for given filter
    objects = StockIOLog.objects.filter(
        **filtered_argument).order_by('-id')[:1]
    if objects.exists():
        # if this queryset exists return the object
        return objects.first()
    return None

def get_rate(_object):
    # This method will return rate based n unit
    rate = 0
    # if object is not none
    if _object is not None:
        # if stock io was stored using secoendery unit
        if _object.secondary_unit_flag:
            rate = _object.rate / _object.conversion_factor
        else:
            # no need to convert as this stock io was stored using primary unit
            rate = _object.rate
    return rate


def get_calculated_price_from_iolog(stock_io_log):
    # Return calculated price
    calculated_price = 0
    if stock_io_log is not None:
        purchase_subtotal, additional_price = stock_io_log.get_purchase_price_info()
        if purchase_subtotal is not None and additional_price is not None:
            trade_price = stock_io_log.get_trade_price()

            ratio_of_additional_cost = get_ratio(
                purchase_subtotal,
                trade_price * stock_io_log.quantity
            )

            vat_per_item = stock_io_log.vat_total / stock_io_log.quantity
            tax_per_item = stock_io_log.tax_total / stock_io_log.quantity
            discount_per_item = \
                stock_io_log.discount_total / stock_io_log.quantity

            new_price = trade_price + vat_per_item + tax_per_item + \
                (((additional_price/100)*ratio_of_additional_cost) /
                 stock_io_log.quantity) - discount_per_item

            calculated_price = round(new_price, 4)
    return calculated_price



def get_purchase_price(stock):
    # Return the rate of last purchase of a stock

    last_obj = get_filtered_stock_io(
        {
            'stock': stock,
            'status': Status.ACTIVE,
            'purchase__isnull': False,
            'purchase__status': Status.ACTIVE,
            'purchase__purchase_type': PurchaseType.PURCHASE,
            'rate__gt': 0
        }
    )
    return get_rate(last_obj), get_calculated_price_from_iolog(last_obj)

def populate_rates_of_stocks(store_point=None):
    # fetch all those stock, who have enty on stock io
    stocks = Stock.objects.filter(
        status=Status.ACTIVE,
        store_point=store_point,
        stocks_io__isnull=False,
    ).only(
        'id',
        'purchase_rate',
        'calculated_price'
    ).distinct()

    count = 0
    for item in tqdm(stocks):
        purchase_rate, calculated_price = get_purchase_price(item)
        if item.purchase_rate != purchase_rate or\
                item.calculated_price != calculated_price:
            stop_stock_signal()
            item.purchase_rate = purchase_rate
            item.calculated_price = calculated_price
            item.save(update_fields=['purchase_rate', 'calculated_price'])
            count += 1
            start_stock_signal()
    logger.info("{} of {} stocks updated".format(count, stocks.count()))


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        logger.info("Fixing Purchase Rate, Calculated Price of Stock based on active purchases")

        # Taking input for an organization
        organization_instance = get_organization_by_input_id()

        # Taking input of a storepoint of given organization
        storepoint_instance = get_storepoint_by_id(
            organization_instance, "Enter Storepoint ID : ")

        populate_rates_of_stocks(storepoint_instance)
        logger.info("Done!")
