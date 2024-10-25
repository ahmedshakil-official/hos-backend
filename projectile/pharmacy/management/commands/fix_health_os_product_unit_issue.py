import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status

from pharmacy.models import Product, StockIOLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    Fixing product unit(Box) for HealthOS
    '''

    def handle(self, **options):
        logger.info("Fixing product unit(Box) for HealthOS")

        valid_unit_id_for_box = 174
        invalid_unit_id_for_box = 171
        organization_id = 303

        products = Product.objects.filter(
            status=Status.ACTIVE,
            organization__id=organization_id
        )
        products.filter(primary_unit__id=invalid_unit_id_for_box).update(primary_unit_id=valid_unit_id_for_box)
        products.filter(secondary_unit__id=invalid_unit_id_for_box).update(secondary_unit_id=valid_unit_id_for_box)

        # ios_with_secondary_unit_flag = StockIOLog.objects.filter(
        #     secondary_unit_flag=True,
        #     organization__id=organization_id
        # ).exclude(status=Status.INACTIVE)
        # io_instances_need_to_update = []

        # for item in ios_with_secondary_unit_flag:
        #     if item.primary_unit_id == invalid_unit_id_for_box:
        #         item.primary_unit_id = valid_unit_id_for_box

        #     if item.secondary_unit_id == invalid_unit_id_for_box:
        #         item.primary_unit_id = valid_unit_id_for_box

        #     if item.secondary_unit_id == item.secondary_unit_id:
        #         item.secondary_unit_flag = False

        #         valid_qty = item.quantity / item.conversion_factor

        #         if valid_qty > 0 and valid_qty.is_integer():
        #             item.quantity = valid_qty
        #     io_instances_need_to_update.append(item)

        # StockIOLog.objects.bulk_update(
        #     io_instances_need_to_update,
        #     ['primary_unit_id', 'secondary_unit_id', 'secondary_unit_flag', 'quantity'],
        #     batch_size=1000
        # )

        logger.info("Done!!!")
