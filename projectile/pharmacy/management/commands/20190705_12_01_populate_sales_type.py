import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from pharmacy.models import Sales
from pharmacy.enums import SalesType
from common.enums import Status
from common.helpers import custom_elastic_rebuild


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("UPDATING CASH SALES")
        sales = Sales.objects.filter(
            status__in=[Status.ACTIVE, Status.DRAFT],
            person_organization_buyer__isnull=True,
            sales_type=SalesType.CREDIT
        )

        update_count = sales.count()

        # update sales_type by CASH
        sales.update(sales_type=SalesType.CASH)

        # custom rebuild all cash sales
        custom_elastic_rebuild(
            'pharmacy.models.Sales', {'sales_type': SalesType.CASH}
        )

        if update_count > 0:
            logger.info("{} SALES UPDATED.".format(update_count))
        else:
            logger.info("NOTHING UPDATED.")
