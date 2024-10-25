import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from common.enums import Status

from pharmacy.models import Sales

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    '''
    populate discount_rate of sales model
    '''

    def handle(self, **options):
        # Check active product and unpopulated product code
        sales = Sales.objects.filter(
            status__in=[Status.ACTIVE, Status.ON_HOLD]
        )
        logger.info("POPULATING SALES")
        update_count = 0

        for sale in tqdm(sales):
            if sale.discount > 0:
                discount_rate = round(
                    float(sale.discount * 100) / sale.amount, 3)
                if sale.discount_rate != discount_rate:
                    sale.discount_rate = discount_rate
                    sale.save(update_fields=['discount_rate'])
                    update_count += 1

        if update_count > 0:
            logger.info("{} SALES UPDATED.".format(update_count))
        else:
            logger.info("NOTHING UPDATED")
