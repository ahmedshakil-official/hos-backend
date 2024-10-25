import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from pharmacy.models import Stock
from common.enums import Status

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        '''
        This script will update  `avg_purchase_rate` field of stock model
        '''
        logger.info("Updating avg purchase rate of stock")

        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            store_point__status=Status.ACTIVE,
            stock__gt=0,
            avg_purchase_rate__lte=0,
            stocks_io__purchase__isnull=False,
        ).distinct()

        for stock in tqdm(stocks):
            stock.update_avg_purchase_rate()

        logger.info("Total {} stock updated.".format(stocks.count()))
