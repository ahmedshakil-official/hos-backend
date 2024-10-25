import os
import logging

from tqdm import tqdm
import pandas as pd
from django.core.management.base import BaseCommand
from projectile.settings import REPO_DIR
from pharmacy.models import ProductCompartment, Stock, Product

logger = logging.getLogger(__name__)


def get_compartments():
    compartments = ProductCompartment().get_all_actives().values("name", "id")
    compartment_data = {}
    for item in compartments:
        compartment_data[item["name"]] = item["id"]
    return compartment_data

def fix_compartment(stock_id_list, compartment_id):
    if stock_id_list and compartment_id:
        stocks = Stock.objects.filter(
            pk__in=stock_id_list
        ).exclude(
            product__compartment_id=compartment_id
        ).only("id", "product_id")
        product_pk_list = stocks.values_list('product_id', flat=True)
        Product.objects.filter(pk__in=product_pk_list).update(compartment_id=compartment_id)


class Command(BaseCommand):
    def handle(self, **options):
        logger.info("Fixing Product Compartment....")
        file_location = os.path.join(REPO_DIR, "tmp/fix_compartment_list.xlsx")
        xl = pd.ExcelFile(file_location)
        sheets = xl.sheet_names
        compartments = get_compartments()
        for sheet in tqdm(sheets):
            logger.info(f"Fixing Product Compartment for {sheet}")
            data = xl.parse(sheet)
            data = data[["ID"]]
            data = data.dropna(subset=["ID"])
            compartment_id = compartments.get(sheet, 0)
            data_df = data.astype({'ID':'int'})
            id_list = data_df['ID'].tolist()
            fix_compartment(id_list, compartment_id)
        logger.info("Done !!!")
