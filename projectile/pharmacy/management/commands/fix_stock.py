import logging

from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand
from pharmacy.models import StorePoint, Stock, Product
from common.enums import PublishStatus

logger = logging.getLogger(__name__)


def fix_stock():
    store_points = StorePoint.objects.all()
    products = Product.objects.filter(
        (Q(is_global=PublishStatus.INITIALLY_GLOBAL) | Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL)))
    stock_count = 0

    for store_point in tqdm(store_points):
        for product in products:
            stocks = Stock.objects.filter(
                store_point=store_point,
                product=product
            ).order_by('pk')
            if stocks.exists():
                Stock.objects.exclude(id=stocks[0].id).filter(
                    store_point=store_point,
                    product=product
                ).delete()
                stock_count += 1
    logger.info("{} Stock updated for {}".format(stock_count, store_point))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        fix_stock()
