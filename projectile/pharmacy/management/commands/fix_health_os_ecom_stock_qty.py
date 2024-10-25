import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.cache import cache

from common.enums import Status
from common.cache_keys import STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX

from core.models import  Organization

from pharmacy.models import Stock, Product
from pharmacy.utils import get_is_queueing_item_value

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    Fixing stock quantity calculating related ioLogs for HealthOS E-Commerce
    '''

    def handle(self, **options):

        try:
            healthos_org_instance = Organization.objects.only('id').get(
                pk=303
            )
        except Organization.DoesNotExist:
            healthos_org_instance = Organization.objects.only('id').get(
                pk=41
            )

        settings = healthos_org_instance.get_settings()

        total_update_count = 0
        stock_instances = []
        product_instances = []
        stock_cache_key_list = []


        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            organization__id=healthos_org_instance.id,
            store_point__status=Status.ACTIVE
        ).only('id', 'ecom_stock', 'orderable_stock', 'product__name')
        for stock in tqdm(stocks):
            calculated_stock = stock.get_calculated_stock_for_ecommerce()
            current_orderable_stock = stock.get_current_orderable_stock(calculated_stock)
            if stock.ecom_stock != calculated_stock or stock.orderable_stock != current_orderable_stock:
                logger.info(
                    "{} PREV Q : {} CALCULATED QTY : {}".format(
                        stock.product.name.ljust(40),
                        str(stock.ecom_stock).ljust(10),
                        str(calculated_stock).ljust(10)
                    )
                )
                stock.ecom_stock = calculated_stock
                stock.orderable_stock = current_orderable_stock
                stock_instances.append(stock)
                total_update_count += 1
            # Check if product is_queueing_item should change or not
            product = Product.objects.only('order_mode', 'is_queueing_item').get(pk=stock.product_id)
            is_queueing_item_value = get_is_queueing_item_value(
                stock.orderable_stock,
                product.order_mode,
                settings
            )
            if is_queueing_item_value != product.is_queueing_item:
                product.is_queueing_item = is_queueing_item_value
                product_instances.append(product)
                logger.info(
                    f"Set product is queueing item to {is_queueing_item_value} for stock {stock.id}."
                )
            stock_key_list = [
                # f"stock_instance_{str(stock).zfill(12)}",
                f"{STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX}_{str(stock.id).zfill(12)}"
            ]
            stock_cache_key_list.extend(stock_key_list)
        Stock.objects.bulk_update(stock_instances, ['orderable_stock', 'ecom_stock'], batch_size=1000)
        Product.objects.bulk_update(product_instances, ['is_queueing_item',], batch_size=1000)
        # Expire stock cache
        cache.delete_many(stock_cache_key_list)


        logger.info(
            '-------------------------------------------------------------------')

        report = """
        total update count = {}"""

        logger.info(report.format(
            total_update_count,
        ))
