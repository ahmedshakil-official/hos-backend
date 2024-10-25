import logging

from tqdm import tqdm

from django.core.management.base import BaseCommand

from pharmacy.models import StockAdjustment
from pharmacy.enums import DisbursementFor

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def populate_flag(self):

        logger.info("Populating Product Disbursement")

        # finding all product disbursement type adjustment
        disbursements = StockAdjustment.objects.filter(
            is_product_disbrustment=True)

        for disbursement in tqdm(disbursements):

            # if disbursement type patient
            if disbursement.service_consumed is None:
                disbursement.disbursement_for = DisbursementFor.PATIENT
            # if disbursement type is service consume
            else:
                disbursement.disbursement_for = DisbursementFor.SERVICE_CONSUMED
            disbursement.save()

    def handle(self, **options):
        self.populate_flag()
