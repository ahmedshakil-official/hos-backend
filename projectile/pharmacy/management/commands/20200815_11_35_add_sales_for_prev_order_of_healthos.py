import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from common.enums import Status
from core.enums import OrganizationType
from core.models import Person
from pharmacy.models import Purchase
from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        '''
        This script will add sales for all previous completed order
        '''
        logger.info("Adding sales for all previous orders")
        allowed_status_for_sales = [OrderTrackingStatus.ON_THE_WAY, OrderTrackingStatus.COMPLETED]
        orders = Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
            sales__isnull=True,
            distributor__pk=303,
        )
        sale_count = 0

        for order in tqdm(orders):
            if order.current_status in allowed_status_for_sales:
                tracking_instance = order.order_status.filter(
                    order_status__in=allowed_status_for_sales).order_by('order_status').first()
                if tracking_instance:
                    if tracking_instance.entry_by:
                        _user = tracking_instance.entry_by
                        sale_date = tracking_instance.date
                    else:
                        _user = Person.objects.get(pk=1015)
                        sale_date = None
                    order.perform_sale_for_order(_user, sale_date)
                    sale_count += 1
        logger.info("Done!! Total {} Sale added.".format(sale_count))
