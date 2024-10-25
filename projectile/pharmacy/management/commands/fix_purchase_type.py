import logging

from django.core.management.base import BaseCommand
from pharmacy.models import Purchase
from ...enums import PurchaseType
from common.enums import Status
logger = logging.getLogger(__name__)


def fix_purchase_type():
    logger.info("FIX PURCHASE TYPE....")
    purchase_type_fix_count = Purchase.objects.count()
    try:
        Purchase.objects.filter(status=Status.ACTIVE).update(purchase_type=PurchaseType.PURCHASE)
        Purchase.objects.filter(status=Status.DRAFT).update(purchase_type=PurchaseType.REQUISITION)
        Purchase.objects.filter(status=Status.PURCHASE_ORDER).update(purchase_type=PurchaseType.PURCHASE)

    except (AttributeError, IndexError, EOFError, IOError) as exception:
        logger.exception(exception)

    logger.info("{} Purchase Type Fixed.".format(purchase_type_fix_count))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        fix_purchase_type()
