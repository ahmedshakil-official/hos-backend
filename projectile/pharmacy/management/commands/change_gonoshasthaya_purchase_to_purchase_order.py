import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.enums import Status
from core.models import Organization
from pharmacy.models import Purchase, StockIOLog

logger = logging.getLogger(__name__)


def change_purchase_to_purchase_order(self):
    logger.info("CHANGING PURCHASE TO PURCHASE ORDER")
    organization = Organization.objects.filter(
        status=Status.ACTIVE,
        name__icontains='Gonoshasthaya')
    purchases = Purchase.objects.filter(
        status=Status.ACTIVE,
        organization=organization
        )
    purchase_count = 0

    for purchase in tqdm(purchases):

        stock_io_logs = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=organization,
            purchase=purchase,
            )
        for stock_io_log in stock_io_logs:
            if stock_io_log.stock.stock > 0:
                stock_io_log.stock.stock = stock_io_log.stock.stock - stock_io_log.quantity
                stock_io_log.stock.save(update_fields=['stock'])
                stock_io_log.status = Status.PURCHASE_ORDER
                stock_io_log.save(update_fields=['status'])
                stock_io_log.purchase.status = Status.PURCHASE_ORDER
                stock_io_log.purchase.save(update_fields=['status'])
        purchase_count += 1
    logger.info("{} Purchase Changed to Purchase Order".format(purchase_count))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        change_purchase_to_purchase_order(self)
