"""
Management script for adding product and stock display_name that do not have any display name.
"""
import os
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q
from tqdm import tqdm

from common.enums import Status

from pharmacy.helpers import get_product_short_name
from pharmacy.models import Product, Stock

logger = logging.getLogger(__name__)


# get organization id
organization_id = os.environ.get("DISTRIBUTOR_ORG_ID", 303)


def populate_product_display_name():
    """A function to populate display name of the product that do not have display name."""
    products = Product.objects.filter(
            organization_id=organization_id,
            status=Status.ACTIVE
            ).filter(
            Q(display_name__isnull=True) |
            Q(display_name="")
    )

    try:
        count = 0
        product_updates = []
        for product in tqdm(products):
            product_updates.append(
                Product(
                    id=product.id,
                    display_name=get_product_short_name(product),
                    organization_id=product.organization_id,
                )
            )
            count += 1

        Product.objects.bulk_update(product_updates, ["display_name"])

        logger.info("%s products display name updated!", count)

    except Exception as e:
        pass


def populate_stock_display_name():
    """A function to populate display name of the stock that do not have display name or mismatch with product."""
    products = Product.objects.filter(
        organization_id=organization_id,
        status=Status.ACTIVE,
    )
    count = 0

    # updating stock display name as product display name.
    try:
        for product in tqdm(products):
            Stock.objects.filter(
                organization_id=product.organization_id,
                status=Status.ACTIVE,
                product_id=product.id,
                ).filter(
                ~Q(display_name=product.display_name)
                ).update(
                display_name=get_product_short_name(product)
            )
            count += 1

        logger.info("%s Stock display name updated!", count)

    except Exception as e:
        pass


class Command(BaseCommand):
    """Django Command to populate product and stock display_name."""

    def handle(self, **options):
        """Entry point for command."""
        logger.info("Management script for populate display name started!")

        populate_product_display_name()

        populate_stock_display_name()

        logger.info("Product and Stock display_name updated Done!")
