import logging

from django.db import connection
from django.core.management.base import BaseCommand

from pharmacy.models import (
    Product,
    ProductAdditionalInfo,
    OrganizationWiseDiscardedProduct
)
from pharmacy.enums import GlobalProductCategory

from common.enums import Status

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):

        # removing record from cloned product
        cloned_products = Product.objects.filter(
            clone__global_category=GlobalProductCategory.GPB
        )
        cloned_products.update(
            clone=None
        )

        # Deleting all stock record
        cursor = connection.cursor()
        cursor.execute(
            'DELETE FROM pharmacy_stock USING pharmacy_product WHERE \
            pharmacy_stock.product_id = pharmacy_product.id AND \
            pharmacy_stock.status = %s AND pharmacy_product.global_category = %s',
            [Status.INACTIVE, GlobalProductCategory.GPB]
        )
        connection.commit()

        # deleting discared product entry
        discarded_products = OrganizationWiseDiscardedProduct.objects.filter(
            parent__global_category=GlobalProductCategory.GPB
        )
        discarded_products.delete()

        # deleting additional product info
        product_info = ProductAdditionalInfo.objects.filter(
            product__global_category=GlobalProductCategory.GPB
        )
        product_info.delete()

        products = Product.objects.filter(
            global_category=GlobalProductCategory.GPB
        )

        products.delete()
