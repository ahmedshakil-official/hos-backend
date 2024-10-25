import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.models import Organization
from pharmacy.models import Purchase, Sales

logger = logging.getLogger(__name__)


def fix_storepoint(organization):
    logger.info("Populating Store Point for Orders")
    _store_point = organization.get_settings().default_storepoint

    # fetching orders for missing store
    purchases = Purchase.objects.filter(
        store_point__isnull=True,
        distributor=organization
    ).update(store_point=_store_point)

    cache.delete_pattern("purchase_distributor_order_*", itersize=10000)

    logger.info("Populating Store Point for Sales")

    # fetching sales for missing store
    sales = Sales.objects.filter(
        store_point__isnull=True,
        organization=organization
    ).update(store_point=_store_point)

    cache.delete_pattern("pharmacy_serializers_sale*", itersize=10000)

    logger.info("Done!!! {} Order and {} Sale Updated.".format(purchases, sales))



class Command(BaseCommand):
    def handle(self, **options):
        logger.info("Populating missing Store Point for HealthOS.")
        organization = Organization.objects.get(pk=303)
        fix_storepoint(organization)
