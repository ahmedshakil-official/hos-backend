import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from pharmacy.models import Purchase, PurchaseRequisition


logger = logging.getLogger(__name__)

def populate_purchase_requisitions_by_copied_from():
    logger.info("UPDATING REQUISITIONS OF PURCHASES")
    purchases = Purchase.objects.filter(
        copied_from__isnull=False)
    update_count = 0
    if purchases.exists():
        for purchase in tqdm(purchases):
            query = PurchaseRequisition.objects.filter(
                organization=purchase.organization,
                purchase=purchase,
                requisition=purchase.copied_from
            )
            if not query.exists():
                purchase_requisition = PurchaseRequisition.objects.create(
                    organization=purchase.organization,
                    purchase=purchase,
                    requisition=purchase.copied_from
                )
                purchase_requisition.save()
                update_count += 1
        logger.info("{} PURCHASES UPDATED.".format(update_count))

    else:
        logger.info("NOTHING UPDATED")

class Command(BaseCommand):
    def handle(self, **options):
        populate_purchase_requisitions_by_copied_from()
