import copy
import logging

from datetime import datetime
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status

from ecommerce.models import OrderInvoiceGroup

from pharmacy.enums import OrderTrackingStatus, DistributorOrderType, PurchaseType
from pharmacy.models import Purchase, OrderTracking

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Cancel Older Orders those are Still Pending or Accepted")

        start_date = datetime(2021, 7, 1)
        end_date = datetime(2023, 10, 10)

        # Define the filters to select specific purchases
        filters = {
            "tentative_delivery_date__range": (start_date, end_date),
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "current_order_status__in": [OrderTrackingStatus.PENDING, OrderTrackingStatus.ACCEPTED]
        }

        # Filter purchases with the specified date range , types and statuses
        purchases_to_update = Purchase.objects.filter(
            **filters
        )

        # Use list comprehension to get the IDs of purchases
        updated_purchase_ids = copy.copy(purchases_to_update.values_list('id', flat=True))

        # creating order tracking objects that will also update the order status
        for purchase_id in tqdm(updated_purchase_ids):
            try:
                OrderTracking.objects.create(
                    order_status=OrderTrackingStatus.CANCELLED,
                    order_id=purchase_id
                )
            except:
                continue

        # Update the status to CANCELED for the associated OrderInvoiceGroups
        OrderInvoiceGroup.objects.filter(
            orders__id__in=updated_purchase_ids
        ).update(current_order_status=OrderTrackingStatus.CANCELLED)

        logger.info(f"Updated total {updated_purchase_ids.count()} Purchases and related models status to cancel")