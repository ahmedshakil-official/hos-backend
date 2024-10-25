from django.core.management.base import BaseCommand
from ecommerce.models import OrderInvoiceGroup
import logging
from tqdm import tqdm

from common.enums import Status

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info("Populate Shorts and Returns and save to DB")
        order_invoice_groups = OrderInvoiceGroup.objects.filter(status=Status.ACTIVE)
        obj_to_be_updated = []
        for order_invoice_group in tqdm(order_invoice_groups):
            obj_to_be_updated.append(
                OrderInvoiceGroup(
                    id=order_invoice_group.id,
                    total_short=order_invoice_group.short_total,
                    total_return=order_invoice_group.return_total
                )
            )

        OrderInvoiceGroup.objects.bulk_update(
            objs=obj_to_be_updated,
            fields=['total_short', 'total_return'],
            batch_size=100,
        )
