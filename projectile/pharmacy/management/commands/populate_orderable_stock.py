import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from common.enums import Status
from common.helpers import is_allowed_to_update_queueing_item_value
from core.models import Organization
from pharmacy.models import Stock, Product
from pharmacy.helpers import stop_inventory_signal, start_inventory_signal

logger = logging.getLogger(__name__)


def populate_orderable_stock():

    try:
        distributor_org = Organization.objects.get(
            pk=303
        )
    except Organization.DoesNotExist:
        distributor_org = Organization.objects.get(
            pk=41
        )

    settings = distributor_org.get_settings()

    update_count = 0
    stocks = Stock.objects.filter(
        status=Status.ACTIVE,
        organization=distributor_org,
        store_point__status=Status.ACTIVE,
    )
    stop_inventory_signal()
    for stock in tqdm(stocks):
        current_orderable_stock = stock.current_orderable_stock
        if current_orderable_stock != stock.orderable_stock:
            stock.orderable_stock = current_orderable_stock
            update_count += 1
            stock.save(update_fields=['orderable_stock'])
        # Update Next Day Flag
        if stock.orderable_stock <= 0 and is_allowed_to_update_queueing_item_value(settings, stock.product):
            Product.objects.filter(
                pk=stock.product_id,
                is_queueing_item=False
            ).update(is_queueing_item=True)
        else:
            Product.objects.filter(
                pk=stock.product_id,
                is_queueing_item=True
            ).update(is_queueing_item=False)
        stock.expire_cache()
    logger.info(f"Total {update_count} stock updated.")
    start_inventory_signal()


class Command(BaseCommand):
    def handle(self, **options):
        populate_orderable_stock()
