import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status
from pharmacy.models import Sales

logger = logging.getLogger(__name__)


def populate_data():

    logger.info("Populating editable field in Sales")

    items = Sales.objects.filter(
        status=Status.ACTIVE,
        editable=False,
        sales_for_service_consumed_group__isnull=True,
        appointmentserviceconsumed__isnull=True,
        sales_discount__isnull=True,
        return_sales_for_purchase__isnull=True
    )
    update_count = items.count()
    items.update(editable=True)
    logger.info("{} Sales updated.".format(update_count))


class Command(BaseCommand):
    '''
    This management script populate editable field
    of Sales model which only contain transaction or single
    '''

    def handle(self, **options):
        populate_data()
