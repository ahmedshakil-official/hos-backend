import logging
from django.core.management.base import BaseCommand
from common.enums import Status
from pharmacy.enums import StockIOType, AdjustmentType

from pharmacy.models import StockIOLog, StockAdjustment

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, **options):
        # get all inactive sales
        stock_io_logs = StockIOLog.objects.filter(
            status=Status.INACTIVE,
            sales__isnull=False,
            sales__copied_from__isnull=True,
            type=StockIOType.OUT,
        )
        logger.info("UPDATING ADJUSTMENT STOCK IO LOG")
        update_count = 0

        for io_log in stock_io_logs:
            if io_log.organization.organizationsetting.auto_adjustment and \
                    io_log.stock.store_point.auto_adjustment:
                try:
                    # get adjustment with io log organization and stock store point
                    stock_adjustment = StockAdjustment.objects.get(
                        organization=io_log.organization,
                        status=Status.ACTIVE,
                        adjustment_type=AdjustmentType.AUTO,
                        store_point=io_log.stock.store_point,
                    )

                    # find all active stock io log with this adjustment
                    adjustment_stock_io = StockIOLog.objects.filter(
                        adjustment=stock_adjustment,
                        status=Status.ACTIVE,
                        type=StockIOType.INPUT,
                        stock=io_log.stock,
                        date=io_log.date,
                        quantity=io_log.quantity,
                        rate=io_log.rate,
                        batch=io_log.batch,
                        secondary_unit_flag=io_log.secondary_unit_flag,
                        primary_unit=io_log.primary_unit,
                        secondary_unit=io_log.secondary_unit,
                    )

                    # update status
                    for adjustment_stock in adjustment_stock_io:
                        adjustment_stock.status = Status.INACTIVE
                        adjustment_stock.save(update_fields=['status'])
                        update_count += 1

                except StockAdjustment.MultipleObjectsReturned, StockAdjustment.DoesNotExist:
                    logger.info("Duplicate or None Stock adjustment found!")

        if update_count > 0:
            logger.info("{} STOCK IO LOG UPDATED OF ADJUSTMENT.".format(update_count))
        else:
            logger.info("NOTHING UPDATED")
