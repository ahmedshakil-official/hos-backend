import os
import logging
import pandas as pd

from django.core.management.base import BaseCommand

from pharmacy.models import Stock, Product
from projectile.settings import REPO_DIR
from search.utils import update_stock_es_doc

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Management script for update daily order limits for Mirpur and Uttara"""

        file_path = "tmp/delivery-hub-order-limit-per-day.xlsx"
        file_location = os.path.join(REPO_DIR, file_path)

        if not os.path.exists(file_location):
            logger.error(f"File '{file_path}' does not exist.")
            return

        try:
            excel_data = pd.read_excel(file_location)
            stock_ids = excel_data["STOCK_ID"].tolist()
            stock_id_to_mirpur_limit = dict(
                zip(excel_data["STOCK_ID"], excel_data["MIRPUR_LIMIT"])
            )
            stock_id_to_uttara_limit = dict(
                zip(excel_data["STOCK_ID"], excel_data["UTTARA_LIMIT"])
            )
            stock_id_to_adabor_limit = dict(
                zip(excel_data["STOCK_ID"], excel_data["ADABOR_LIMIT"])
            )

            # Fetch all stock with stock_ids
            stocks = Stock().get_all_actives().filter(pk__in=stock_ids).select_related("product")

            retrieved_stock_ids = set(stocks.values_list("pk", flat=True))
            missing_stock_ids = set(stock_ids) - retrieved_stock_ids

            product_updates = []

            for stock in stocks:
                mirpur_limit = stock_id_to_mirpur_limit.get(stock.pk, None)
                uttara_limit = stock_id_to_uttara_limit.get(stock.pk, None)
                adabor_limit = stock_id_to_adabor_limit.get(stock.pk, None)

                if mirpur_limit is not None:
                    stock.product.order_limit_per_day_mirpur = mirpur_limit
                if uttara_limit is not None:
                    stock.product.order_limit_per_day_uttara = uttara_limit
                if adabor_limit is not None:
                    stock.product.order_limit_per_day = adabor_limit

                logger.info(
                    f"Updated order limits for Stock ID {stock.pk} and Product '{stock.product.name}'"
                )
                product_updates.append(stock.product)

            Product.objects.bulk_update(
                product_updates,
                [
                    "order_limit_per_day",
                    "order_limit_per_day_mirpur",
                    "order_limit_per_day_uttara",
                ],
            )

            logger.info("Order limits updated successfully.")

            if missing_stock_ids:
                for stock_id in missing_stock_ids:
                    company_name = excel_data.loc[excel_data["STOCK_ID"] == stock_id][
                        "COM"
                    ].values[0]
                    logger.warning(f"Missing Stock IDs {stock_id} for {company_name}")

            update_stock_es_doc(queryset=stocks)

        except Exception as e:
            logger.error(f"An error occurred: {e}")
