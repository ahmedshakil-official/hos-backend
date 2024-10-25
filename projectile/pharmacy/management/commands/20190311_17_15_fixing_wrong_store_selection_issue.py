import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from common.enums import Status
from pharmacy.models import (
    Stock, StockIOLog
)
from pharmacy.signals import (
    pre_save_stock_io_log,
    pre_save_stock
)
from django.db.models.signals import pre_save

logger = logging.getLogger()


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("UPDATING STOCK ACCORDING TO SALES")
        stock_ios = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization__pk=1
        ).exclude(
            sales__isnull=True
        ).select_related(
            'sales',
            'stock',
            'stock__product'
        ).filter(
            ~Q(sales__store_point=F('stock__store_point'))
        )

        for _item in tqdm(stock_ios):

            # get proper stock
            correct_stock = Stock.objects.filter(
                store_point=_item.sales.store_point,
                product=_item.stock.product,
                status=Status.ACTIVE,
            ).first()

            item = StockIOLog.objects.get(
                pk=_item.pk
            )

            # checking if quantity is not violating constrain
            if correct_stock.stock >= item.quantity:
                product_qty = item.quantity

                # disconnecting signal
                pre_save.disconnect(pre_save_stock_io_log, StockIOLog)
                pre_save.disconnect(pre_save_stock, Stock)

                # reducing stock of current stock io's stock
                correct_stock.stock = correct_stock.stock - product_qty
                correct_stock.save()

                # incresing stock of current sales's storepoint
                item.stock.stock = item.stock.stock + product_qty
                item.stock.save()

                # chaning stock io of stock io
                item.stock = correct_stock
                item.save()

                # re-connecting signal
                pre_save.connect(pre_save_stock_io_log, StockIOLog)
                pre_save.connect(pre_save_stock, Stock)
            else:
                logger.error(
                    "not enough stock on {}, for {} should be at least {},\
                    current is {}".format(
                        correct_stock.store_point.name,
                        correct_stock.product.name,
                        item.quantity,
                        correct_stock.stock
                    )
                )
