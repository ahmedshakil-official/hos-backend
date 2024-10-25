import re
import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from common.enums import Status
from pharmacy.models import (
    Stock,
)


logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        raw_query='''
            SELECT DATA.stock_id AS id, DATA.* FROM (
            SELECT stock_info.*,
                correct_stock.id AS correct_stock
            FROM   (SELECT *

                    -- start : this gives stock info of all discarded parent product

                    FROM   (SELECT stock_id ,
                                stock.organization_id,
                                store_point_id,
                                discarded.product_id AS correct_product,
                                discarded.parent_id  AS problematic_product
                            FROM   (SELECT id AS stock_id,
                                        product_id,
                                        store_point_id,
                                        organization_id
                                    FROM   pharmacy_stock
                                    WHERE  status = 0) AS stock
                                LEFT JOIN pharmacy_organizationwisediscardedproduct AS
                                            discarded
                                        ON stock.product_id = discarded.parent_id
                                            AND stock.organization_id =
                                                discarded.organization_id
                            WHERE  discarded.product_id IS NOT NULL) AS DATA

                    -- end : this gives stock info of all discarded parent product

                    WHERE  stock_id NOT IN (SELECT DISTINCT stock_id
                                            FROM   pharmacy_stockiolog)) AS stock_info

                -- filter : this made sure this stock were not used in stock io
                -- join start: we want to fetch stock info for product_id of each row found above

                LEFT JOIN (SELECT *
                            FROM   pharmacy_stock
                            WHERE  status = 0) AS correct_stock
                        ON correct_product = correct_stock.product_id
                            AND stock_info.store_point_id = correct_stock.store_point_id
                -- join ends: we want to fetch stock info for product_id of each row found above
            ) AS DATA WHERE correct_stock IS NOT NULL
            -- filter: discard those row what does not have possible correct stock
        '''

        stocks = Stock.objects.raw(raw_query)

        for stock in tqdm(stocks):
            possible_correct_stock = Stock.objects.get(pk=stock.correct_stock)

            if re.sub(r"\W", "", stock.product_full_name).lower() == re.sub(r"\W", "", possible_correct_stock.product_full_name).lower() and possible_correct_stock.organization == stock.organization:
                stock.status = Status.INACTIVE
                stock.save(update_fields=['status'])
