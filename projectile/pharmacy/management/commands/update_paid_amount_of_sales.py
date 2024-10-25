import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status
from pharmacy.models import Sales


logger = logging.getLogger(__name__)

def update_paid_amount_of_sales():
    logger.info("UPDATING PAID_AMOUNT OF SALES")
    sales = Sales.objects.filter(
        status=Status.ACTIVE, transaction_of__isnull=False)
    update_count = 0
    if sales.exists():
        for sale in tqdm(sales):
            transactions = sale.transaction_of.filter(
                status=Status.ACTIVE).only('id', 'amount')
            paid_amount = sum([item.amount for item in transactions])
            if sale.paid_amount != paid_amount:
                sale.paid_amount = paid_amount
                sale.save(update_fields=['paid_amount'])
                update_count += 1
        logger.info("{} SALES UPDATED.".format(update_count))

    else:
        logger.info("NOTHING UPDATED")

class Command(BaseCommand):
    def handle(self, **options):
        update_paid_amount_of_sales()
