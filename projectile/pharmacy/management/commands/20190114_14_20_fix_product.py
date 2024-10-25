import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from common.helpers import get_storepoint_by_product as get_storepoint

from common.enums import Status

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):

        from pharmacy.models import Product, Stock, StockIOLog

        product = {
            # list of problamatic products id
            'problamatic': [8477, 8480, 8522, 8523, 8531, 8556, 8557, 8570, 8583, 8603],
            # list of alternative products id
            'alternative': [22479, 28143, 13759, 13760, 39385, 34754, 34755, 19759, 9207, 14130]
        }

        # getting all storepoint associated with product['problamatic'], note this will contain an
        # attribute `problamatic_stock` which will contain individual information of each item of product['problamatic']
        storepoints = get_storepoint(product['problamatic'])

        for storepoint in tqdm(storepoints):
            for stock_entry in storepoint.problamatic_stock:

                problamatic_product = stock_entry.product

                # product['problamatic'].index(stock_entry.product.pk) gives us the index of
                # stock_entry.product.pk in 'product[problamatic]'
                index = product['problamatic'].index(stock_entry.product.pk)

                # find correct product to be replaced with
                replace_with = Product.objects.get(
                    pk=product['alternative'][index]
                )

                # all stocks
                stocks = Stock.objects.filter(
                    store_point=storepoint,
                    status=Status.ACTIVE,
                )

                # faulty stock instance
                prev_stock = stocks.get(
                    product=problamatic_product,
                    status=Status.ACTIVE
                )

                # all stock io instance
                items = StockIOLog.objects.filter(
                    stock=prev_stock
                )

                # if number of stock io with this product is greater then zero
                try:
                    if items.count() > 0:
                        prev_stock.product = replace_with
                        prev_stock.save()

                    # if no stock io log was entered
                    else:
                        prev_stock.status = Status.INACTIVE
                        prev_stock.save()
                except IntegrityError as exception:
                    logger.exception(exception)
