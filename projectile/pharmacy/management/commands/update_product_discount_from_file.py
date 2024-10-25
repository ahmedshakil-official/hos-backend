import os
import logging
from datetime import datetime

from tqdm import tqdm
import pandas as pd
from django.core.cache import cache
from django.apps import apps
from django.core.management.base import BaseCommand
from projectile.settings import REPO_DIR
from pharmacy.models import Stock, Product, ProductChangesLogs
from search.utils import update_stock_es_doc

logger = logging.getLogger(__name__)


def get_data(df, stock_id, key):
    try:
        return df.loc[(df.stock__id == stock_id)][key].values[0]
    except:
        try:
            return df.loc[(df.ID == stock_id)][key].values[0]
        except:
            return 0


class Command(BaseCommand):
    def handle(self, **options):
        logger.info("Updating Product Discount from File....")
        file_location = os.path.join(REPO_DIR, "tmp/stock_list_for_discount_update.xlsx")
        stock_data = pd.read_excel(file_location)
        stock_id_list = stock_data["ID"].to_list()
        stock_qs = Stock.objects.filter(pk__in=stock_id_list)
        update_count = 0
        products_to_be_updated = []
        product_changes_log_data = []
        stock_key_list = []
        for stock in tqdm(stock_qs):
            product_discount_rate = round(get_data(stock_data, stock.id, "NEW_DISCOUNT"), 2)
            product = Product.objects.only("discount_rate", "image").get(pk=stock.product_id)
            current_discount = round(product.discount_rate, 2)
            if product_discount_rate and product_discount_rate != current_discount:
                product.discount_rate = product_discount_rate
                products_to_be_updated.append(product)
                stock_key_list.append('stock_instance_distributor_{}'.format(str(stock.id).zfill(12)))
                product_changes_log_data.append(
                    ProductChangesLogs(
                        product_id=stock.product_id,
                        discount_rate={
                            "New": product_discount_rate,
                            "Previous": current_discount,
                        },
                        organization_id=303,
                        date=datetime.now(),
                    )
                )
                update_count += 1
        if update_count:
            # Update Products
            Product.objects.bulk_update(products_to_be_updated, ["discount_rate"])
            # Create product change log
            ProductChangesLogs.objects.bulk_create(product_changes_log_data)
            # Update stock document
            update_stock_es_doc(queryset=stock_qs)
            # Delete cache
            cache.delete_many(stock_key_list)
        logger.info(f"Done !!!, {update_count} Products Updated.")
