import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.enums import Status
from pharmacy.models import Stock, StockIOLog

logger = logging.getLogger()


def get_unit(obj):
    # this method return unit for given stock io log
    unit = None
    # if object is not none
    if obj is not None:
        # if stock io was stored using secoendery unit
        if obj.secondary_unit_flag:
            unit = obj.secondary_unit
        else:
            # stock io was stored using primary unit
            unit = obj.primary_unit
    return unit


def get_latest_sale_or_purchase(stock_instance, is_sale=False):
    # this method filter the last sale or purchase entry of a stock
    # return last sale or purchase unit
    args = {
        'stock': stock_instance,
        'status': Status.ACTIVE,
    }
    if is_sale:
        args['sales__isnull'] = False
    else:
        args['purchase__isnull'] = False

    obj = StockIOLog.objects.filter(
        **args
    ).order_by('-id')[:1]
    if obj.exists():
        # if this queryset exists returing last entry by using -id and [0]
        obj = obj[0]
    else:
        obj = None
    return get_unit(obj)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("UPDATING STOCK LATEST SALE AND PURCHASE UNIT")
        update_count = 0

        # fetch all those stock, what have enty on stock io
        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            product__status=Status.ACTIVE,
            store_point__status=Status.ACTIVE,
            stocks_io__isnull=False,
            latest_sale_unit__isnull=True,
            latest_purchase_unit__isnull=True
        ).only(
            'product__id',
            'store_point__id'
        ).select_related(
            'product',
            'store_point',
        ).distinct()

        for item in tqdm(stocks):
            # travarse through each item : Stock
            item.latest_sale_unit = get_latest_sale_or_purchase(item, is_sale=True)
            item.latest_purchase_unit = get_latest_sale_or_purchase(item, is_sale=False)
            item.save()
            update_count += 1

        logger.info("{} STOCKS UPDATED.".format(update_count))
