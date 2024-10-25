import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models import Q, F
from django.db.models.signals import pre_save
from common.enums import Status

from pharmacy.models import StockIOLog
from pharmacy.signals import pre_save_stock_io_log

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    Fixing stock io log date using related sales or purchase date
    '''

    def handle(self, **options):
        # Check for active stock io log where purchase date or
        # sale date is not same as stock io log date
        io_logs = StockIOLog.objects.filter(
            status__in=[Status.ACTIVE, Status.DRAFT, Status.PURCHASE_ORDER]
        )
        sales_io_logs = io_logs.filter(
            ~Q(date=F('sales__sale_date')) |
            (Q(date__isnull=True) & Q(sales__isnull=False)),
        )
        purchase_io_logs = io_logs.filter(
            ~Q(date=F('purchase__purchase_date')) |
            (Q(date__isnull=True) & Q(purchase__isnull=False)),
        )

        # Initialize the count as zero(0)
        update_count_for_sales = 0
        update_count_for_purchase = 0
        # Disconnect stock_io_log signal
        pre_save.disconnect(pre_save_stock_io_log, sender=StockIOLog)

        logger.info("FIXING STOCK IO LOG DATE")

        # change the stockIOLog date with related Sales date
        for io_log in tqdm(sales_io_logs):
            # assign the sales date in related stockIOLog
            if io_log.sales.sale_date:
                io_log.date = io_log.sales.sale_date
                # Save the changed date
                io_log.save(update_fields=['date'])
                update_count_for_sales += 1

        # change the stockIOLog date with related purchase date
        for io_log in tqdm(purchase_io_logs):
            if io_log.purchase.purchase_date:
                io_log.date = io_log.purchase.purchase_date
                # Save the changed date
                io_log.save(update_fields=['date'])
                update_count_for_purchase += 1

        # Re connect stock_io_log signal
        pre_save.connect(pre_save_stock_io_log, sender=StockIOLog)

        if update_count_for_sales > 0 or update_count_for_purchase > 0:
            logger.info("{} SALES RELATED STOCK IO LOGS DATE UPDATED.".format(
                update_count_for_sales))
            logger.info("{} PURCHASE RELATED STOCK IO LOGS DATE UPDATED.".format(
                update_count_for_purchase))
        else:
            logger.info("NOTHING UPDATED")
