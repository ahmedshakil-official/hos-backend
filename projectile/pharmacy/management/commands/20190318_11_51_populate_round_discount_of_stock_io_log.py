import logging
from tqdm import tqdm

from django.db.models import Q
from django.core.management.base import BaseCommand
from common.enums import Status

from pharmacy.models import StockIOLog

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    '''
    populate discount_rate of sales model
    '''

    def handle(self, **options):
        stock_io_logs = StockIOLog.objects.filter(
            Q(sales__round_discount__gt=0) |
            Q(purchase__round_discount__gt=0),
            status=Status.ACTIVE
        )
        logger.info("POPULATING STOCK-IO-LOG")
        update_count = 0

        for item in tqdm(stock_io_logs):
            rate = item.rate
            if item.secondary_unit_flag:
                rate = rate / item.conversion_factor
            if item.sales or item.purchase:
                if item.sales:
                    round_discount = float(
                        item.sales.round_discount * item.quantity * rate
                    ) / item.sales.amount
                if item.purchase:
                    round_discount = float(
                        item.purchase.round_discount * item.quantity * rate
                    ) / item.purchase.amount
            if round(item.round_discount, 4) != round(round_discount, 4):
                item.round_discount = round_discount
                item.save(update_fields=['round_discount'])
                update_count += 1

        if update_count > 0:
            logger.info("{} STOCK-IO-LOG UPDATED.".format(update_count))
        else:
            logger.info("NOTHING UPDATED")
