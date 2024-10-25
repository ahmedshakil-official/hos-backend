import logging

from django.db.models import F
from django.core.management.base import BaseCommand

from search.utils import update_stock_es_doc

from pharmacy.models import Product, Stock

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Update order limits for Mirpur and Uttara based on saleability")

        products = Product().get_all_actives().filter(is_salesable=True, organization__id=303)

        products.update(
            order_limit_per_day_mirpur=F('order_limit_per_day'),
            order_limit_per_day_uttara=F('order_limit_per_day')
        )

        product_ids = products.values_list("id", flat=True)
        stock_queryset = Stock().get_all_actives().filter(
            product__id__in=product_ids
        )
        update_stock_es_doc(queryset=stock_queryset)
        logger.info('Successfully updated order limits for Mirpur and Uttara with StockDocument')