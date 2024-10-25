import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from pharmacy.models import Purchase, OrderTracking
from common.enums import Status
from pharmacy.enums import OrderTrackingStatus, PurchaseType, DistributorOrderType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        '''
        This script will update  `current_order_status` field of purchase model
        '''

        orders = Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        )

        for each_order in tqdm(orders):
            tracking = OrderTracking.objects.filter(
                order=each_order
            ).order_by('-id')

            if tracking.exists() and each_order.current_order_status != each_order.current_status:
                each_order.current_order_status = tracking.first().order_status
                each_order.save(update_fields=['current_order_status',])
