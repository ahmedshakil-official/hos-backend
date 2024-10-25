import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Max
from common.enums import Status
from pharmacy.models import Stock

logger = logging.getLogger()


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("Populate product name and length in Stock")

    stocks = Stock.objects.aggregate(Max('id'))
    number_of_item = stocks['id__max']
    chunk_size = 5000
    number_of_operation = int((number_of_item / chunk_size)) + 1

    lower_limit = 0
    upper_limit = chunk_size
    sql_query = """
        UPDATE pharmacy_stock
        SET    product_full_name =  LOWER(concat_ws(' ', pharmacy_product.full_name, pharmacy_product.alias_name)),
            product_len = CASE
                            WHEN
                                pharmacy_product.full_name IS NOT NULL
                                THEN char_length(concat_ws(' ', pharmacy_product.full_name, pharmacy_product.alias_name))
                            ELSE
                                0
                            END
        FROM   pharmacy_product
        WHERE
        pharmacy_product.id = pharmacy_stock.product_id
        AND  LOWER(concat_ws(' ', pharmacy_product.full_name, pharmacy_product.alias_name)) != LOWER(pharmacy_stock.product_full_name)
        AND pharmacy_stock.id BETWEEN {0} AND {1}
        AND pharmacy_product.status = {2}
        AND pharmacy_stock.status = {2};
    """

    for index in tqdm(range(0, number_of_operation)):
        query = sql_query.format(lower_limit, upper_limit, Status.ACTIVE)
        lower_limit = upper_limit + 1
        upper_limit = lower_limit + chunk_size
        with connection.cursor() as cursor:
            cursor.execute(query)
