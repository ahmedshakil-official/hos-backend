import logging
from tqdm import tqdm
from django.db import connection
from django.db.models import Max
from django.core.management.base import BaseCommand
from common.enums import Status


from pharmacy.models import (
    Product, Stock
)
from pharmacy.helpers import (
    stop_product_signal,
    start_product_signal,
    start_stock_signal
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):

        stocks = Stock.objects.aggregate(Max('id'))
        number_of_item = stocks['id__max']
        chunk_size = 5000
        number_of_operation = (number_of_item / chunk_size) + 1

        lower_limit = 0
        upper_limit = chunk_size
        sql_query = """
            UPDATE pharmacy_stock
            SET    status = 1
            FROM   pharmacy_product
            WHERE
            pharmacy_stock.product_id = pharmacy_product.id AND
            pharmacy_product.status = 1 AND pharmacy_stock.status = 0
            AND pharmacy_stock.id BETWEEN {0} AND {1}
        """

        for _ in tqdm(range(0, number_of_operation)):
            query = sql_query.format(lower_limit, upper_limit)
            lower_limit = upper_limit + 1
            upper_limit = lower_limit + chunk_size
            with connection.cursor() as cursor:
                cursor.execute(query)

        lower_limit = 0
        upper_limit = chunk_size

        sql_query = """
            UPDATE pharmacy_stock
            SET    status = pharmacy_product.status,
                   is_salesable = pharmacy_product.is_salesable,
                   is_service = pharmacy_product.is_service
            FROM   pharmacy_product
            WHERE
            pharmacy_stock.product_id = pharmacy_product.id
            AND (pharmacy_product.status != pharmacy_stock.status
            OR pharmacy_stock.is_salesable != pharmacy_stock.is_salesable
            OR pharmacy_stock.is_service != pharmacy_stock.is_service)
            AND pharmacy_stock.id BETWEEN {0} AND {1}
        """

        for _ in tqdm(range(0, number_of_operation)):
            query = sql_query.format(lower_limit, upper_limit)
            lower_limit = upper_limit + 1
            upper_limit = lower_limit + chunk_size
            with connection.cursor() as cursor:
                cursor.execute(query)
