import logging

from django.db.models import Q, F
from django.core.management.base import BaseCommand
from common.enums import Status

from pharmacy.models import Sales, Purchase, StockIOLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    populate round_discount of Sales and Purchase
    '''

    def handle(self, **options):

        # populating round_discount of sales
        logger.info("UPDATING SALES INSTANCE")
        sales = Sales.objects.filter(
            ~Q(status=Status.INACTIVE),
            round_discount__gt=0
        ).update(round_discount=F('round_discount') * -1)
        logger.info("{} SALES INSTANCE UPDATED".format(sales))

        # populating round_discount of purchases
        logger.info("UPDATING PURCHASE INSTANCE")
        purchases = Purchase.objects.filter(
            ~Q(status=Status.INACTIVE),
            round_discount__gt=0
        ).update(round_discount=F('round_discount') * -1)
        logger.info("{} PURCHASE INSTANCE UPDATED".format(purchases))

        # populating round_discount of StockIoLogs
        logger.info("UPDATING IOLOG INSTANCE")
        io_logs = StockIOLog.objects.filter(
            ~Q(status=Status.INACTIVE),
            round_discount__gt=0
        ).update(round_discount=F('round_discount') * -1)
        logger.info("{} STOCKIOLOG INSTANCE UPDATED".format(io_logs))
