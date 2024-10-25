
import logging

from tqdm import tqdm
from django.db.models import Sum, F
from django.core.management.base import BaseCommand
from pharmacy.models import Purchase, StockIOLog

logger = logging.getLogger(__name__)


def fix_purchase():
    logger.info('FIXING PURCHASE AMOUNT')

    io_logs = StockIOLog.objects.exclude(purchase__isnull=True).values('purchase', 'rate', 'quantity').annotate(result=F('quantity')* F('rate')).values_list('purchase','result')

    for io_log in tqdm(io_logs):
        purchase = Purchase.objects.get(id=io_log[0])
        purchase.amount = 0
        purchase.grand_total = 0
        purchase.save()

    for io_log in tqdm(io_logs):
        purchase = Purchase.objects.get(id=io_log[0])
        purchase.amount += io_log[1];
        purchase.grand_total = purchase.amount + purchase.vat_total + purchase.tax_total + purchase.transport
        purchase.save()

    return True


class Command(BaseCommand):

    def handle(self, **options):
        fix_purchase()
