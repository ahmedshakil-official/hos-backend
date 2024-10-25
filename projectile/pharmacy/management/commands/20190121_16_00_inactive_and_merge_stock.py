import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Count, Prefetch, signals

from pharmacy.models import (Product, Stock, StockIOLog)
from pharmacy.signals import (
    pre_save_stock,
    pre_save_stock_io_log
)

from common.helpers import query_yes_no
from common.enums import Status


logger = logging.getLogger(__name__)


def get_stocks_by_store_and_product(store, product, stock_io):
    '''
    this method return all active stock instance for given store and product id
    '''

    # find all stock io with given product and storepoint id
    stock_io_queryset = stock_io.filter(
        stock__store_point__id=store,
        stock__product__id=product,
    )

    # returning all stock with given product and storepoint id along with their
    # relavent stock_io entry
    return Stock.objects.prefetch_related(
        Prefetch('stocks_io',  queryset=stock_io_queryset)
    ).filter(
        store_point=store,
        product=product,
        status=Status.ACTIVE
    )


def merge_stock(primary_stock, secondary_stock, stock_io):
    '''
    this method replace all stock io which belongs to secondary_stock with primary_stock
    and then inactive secondary_stock
    '''
    
    question = "\n\n\nDO YOU WANT TO REPLACE :\n\n {} \n\n WITH \n\n {}\n\n".format(
        secondary_stock, primary_stock)

    # thaking user 's consent
    if query_yes_no(question, "no"):

        # disconnecting all signal related whit this work
        signals.pre_save.disconnect(pre_save_stock, sender=Stock)
        signals.pre_save.disconnect(pre_save_stock_io_log, sender=StockIOLog)

        # finding all stock io related with secondary_stock
        filtered_stock_io = stock_io.filter(
            stock=secondary_stock
        )

        # travarsing through each item of secondary_stock
        for item in filtered_stock_io:
            # replacing with primary_stock
            item.stock = primary_stock
            item.save()

        # making secondary item inactive
        secondary_stock.status = Status.INACTIVE
        secondary_stock.save()

        signals.pre_save.connect(pre_save_stock, sender=Stock)
        signals.pre_save.connect(pre_save_stock_io_log, sender=StockIOLog)


def get_stock_status(querysets):
    '''
    if all duplicate instance in Stock model are provided into querysets
    this method return which Stock should be kept among all those stock
    '''

    # assume first stock entry contains most number of stock io entry
    max_entry_io = querysets.first()
    # assume first stock entry have most stock
    max_stock = querysets.first()
    # assume all stock have zero quantity
    all_zero = True

    # travarse through each stock instance
    for item in querysets:
        # if stock's quantity is greater then zero
        if item.stock > 0:
            # at least one stock instance have stock
            all_zero = False

        # check if this stock have more stock quantity then all previous item
        if item.stock > max_entry_io.stock:
            max_stock = item
        # check if this stock have more stock io entry then all previous item
        if max_stock.stocks_io.count() > item.stocks_io.count():
            max_entry_io = item

    # if all stock have zero quantity
    if all_zero:
        # return which stock have max number of io entry
        return max_entry_io
    else:
        # otherwise return which stock have max stock
        return max_stock


class Command(BaseCommand):

    def handle(self, **options):

        # finding all active stock_io instace
        stock_io = StockIOLog.objects.filter(
            status=Status.ACTIVE
        ).select_related(
            'stock__product',
            'stock__store_point',
        )

        # finding all active stock instance which belong to active storepoint
        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            store_point__status=Status.ACTIVE
        ).select_related(
            'store_point'
        ).values(
            'product', 'store_point'
        ).annotate(
            num_stock=Count('*')
        ).order_by('-num_stock')
        

        # travarsing through each item of stock
        for stock in tqdm(stocks):

            # checking if specific stock contains two entry or not
            if int(stock['num_stock']) >= 2:
                # finding all stock instance with this particular product and storepoint id
                querysets = get_stocks_by_store_and_product(
                    stock['store_point'], stock['product'], stock_io)

                # finding primary stock instance
                primary_stock = get_stock_status(querysets)
                for item in querysets:
                    if item != primary_stock:
                        # making all other stock inactive and replacing their stock in stock io
                        merge_stock(primary_stock, item, stock_io)
            else:
                break
