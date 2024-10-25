import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models.signals import pre_save, post_save
from pharmacy.models import StockIOLog, Product, Stock
from pharmacy.enums import GlobalProductCategory
from pharmacy.signals import (
    pre_save_stock,
    post_save_product
)
from common.enums import PublishStatus, Status

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):

        # Disconnect Product and Stock signal
        post_save.disconnect(post_save_product, Product)
        pre_save.disconnect(pre_save_stock, Stock)

        # finding all entires in stock io in which product belong to GBP

        stock_ios = StockIOLog.objects.filter(
            stock__product__global_category=GlobalProductCategory.GPB
        ).order_by('stock__product__name')

        for io_entry in tqdm(stock_ios):
            product = io_entry.stock.product
            organization = io_entry.organization
            stock = io_entry.stock

            # want to check if same product is used in stock io of any other organization

            any_duplicate_chance = StockIOLog.objects.filter(
                stock__product=product
            ).exclude(
                organization=organization
            )

            if any_duplicate_chance.exists():
                # can't localize this product
                logger.info('product {} can not be localized'.format(product))
            else:
                # we can localize this product

                # changed global category
                product.global_category = GlobalProductCategory.DEFAULT

                # gave an organization
                product.organization = organization

                # changed into private
                product.is_global = PublishStatus.PRIVATE
                product.save(update_fields=['global_category', 'organization', 'is_global'])

                # changed stock related with this product
                stock.status = Status.ACTIVE
                stock.save(update_fields=['status'])
        # Reconnect Product and Stock signal
        post_save.connect(post_save_product, Product)
        pre_save.connect(pre_save_stock, Stock)
