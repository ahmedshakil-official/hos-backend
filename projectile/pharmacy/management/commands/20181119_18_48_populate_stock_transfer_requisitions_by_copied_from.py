import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from pharmacy.models import StockTransfer, StockTransferRequisition


logger = logging.getLogger(__name__)

def populate_stock_transfer_requisitions_by_copied_from():
    logger.info("UPDATING REQUISITIONS OF PURCHASES")
    stock_transfers = StockTransfer.objects.filter(
        copied_from__isnull=False)
    update_count = 0
    if stock_transfers.exists():
        for stock_transfer in tqdm(stock_transfers):
            query = StockTransferRequisition.objects.filter(
                organization=stock_transfer.organization,
                stock_transfer=stock_transfer,
                requisition=stock_transfer.copied_from
            )
            if not query.exists():
                stock_transfer_requisition = StockTransferRequisition.objects.create(
                    organization=stock_transfer.organization,
                    stock_transfer=stock_transfer,
                    requisition=stock_transfer.copied_from
                )
                stock_transfer_requisition.save()
                update_count += 1
        logger.info("{} STOCK TRANSFERS UPDATED.".format(update_count))

    else:
        logger.info("NOTHING UPDATED")

class Command(BaseCommand):
    def handle(self, **options):
        populate_stock_transfer_requisitions_by_copied_from()
