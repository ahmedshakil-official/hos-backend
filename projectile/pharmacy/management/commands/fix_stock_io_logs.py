import logging
from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand
from pharmacy.models import StockIOLog, Purchase
from common.enums import Status

logger = logging.getLogger(__name__)


def fix_stock_io_logs():
    logger.info("UPDATING STOCKIOLOGS")

    # fetching all purchase
    purchases = Purchase.objects.filter(
        status=Status.INACTIVE).values_list('id', flat=True)
    purchases_stock_io_logs = StockIOLog.objects.filter(
        ~Q(status=Status.INACTIVE),
        purchase__id__in=purchases
    )
    purchases_stock_io_logs.update(status=Status.INACTIVE)
    purchases_stock_io_logs_count = 0
    for stock in tqdm(range(purchases_stock_io_logs.count())):
        purchases_stock_io_logs_count += 1

    logger.info("{} StockIoLogs Updated.".format(purchases_stock_io_logs.count()))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        fix_stock_io_logs()
