import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from pharmacy.models import StorePoint, Stock, Product, StockIOLog, Purchase, Sales

logger = logging.getLogger(__name__)


def fix_storepoint():
    logger.info("Updating purchase storepoint")

    # fetching all purchase
    # purchases = Purchase.objects.filter(storepoint__isnull=True)
    purchases = Purchase.objects.all()
    for purchase in tqdm(purchases):
        # finding first stock_io info of purchase

        stock_io = StockIOLog.objects.filter(purchase=purchase)[:1]
        if stock_io.count() > 0:
            purchase.store_point = stock_io[0].stock.store_point
            purchase.save()

    logger.info("Updating sales storepoint")

    # fetching all sales
    # sales = Sales.objects.filter(storepoint__isnull=True)
    sales = Sales.objects.all()

    for sale in tqdm(sales):
        # finding first stock_io info of sale

        stock_io = StockIOLog.objects.filter(sales=sale)[:1]
        if stock_io.count() > 0:
            sale.store_point = stock_io[0].stock.store_point
            sale.save()

    return True


class Command(BaseCommand):
    def handle(self, **options):
        fix_storepoint()
