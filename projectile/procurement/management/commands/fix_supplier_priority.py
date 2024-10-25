import logging
from itertools import chain, repeat
import pandas as pd
from tqdm import tqdm
import math, os, re, difflib
import time
from datetime import datetime
from validator_collection import checkers

from django.core.management.base import BaseCommand
from core.models import ScriptFileStorage

from procurement.models import PredictionItemSupplier
from procurement.enums import RecommendationPriority

logger = logging.getLogger(__name__)





class Command(BaseCommand):
    '''
    This management script will fix the supplier priority
    '''

    def handle(self, **options):
        pur_pred_instance_id = 209
        pred_file_id = 23909
        logger.info(f"Fixing Supplier Priority for file {pred_file_id}")

        stock_file = ScriptFileStorage.objects.only(
            'content', 'entry_by_id', 'purpose',
        ).get(pk=pred_file_id)
        stock_df =  pd.read_excel(stock_file.content)
        columns_from_file = stock_df.columns.to_list()

        pred_item_suppliers = []
        for item in columns_from_file:
            match = re.search("SUPPLIER_S", item)
            if match:
                for li in difflib.ndiff(item, "SUPPLIER_S"):
                    if li[0] == '-':
                        suggested_supplier = li[-1]
                        priority = RecommendationPriority.OTHER if checkers.is_integer(suggested_supplier) and int(suggested_supplier) > 3 else int(suggested_supplier)
                        supplier_col_name = f"SUPPLIER_S{suggested_supplier}"
                        qty_col_name = f"QTY_S{suggested_supplier}"
                        rate_col_name = f"RATE_S{suggested_supplier}"
                        cols = {
                            "supplier": supplier_col_name,
                            "qty": qty_col_name,
                            "rate": rate_col_name,
                            "priority": priority
                        }
                        pred_item_suppliers.append(cols)
        for index, item in tqdm(stock_df.iterrows()):
            try:
                stock_id = item.get('ID', '')
                # Create item suppliers
                for item_supplier in pred_item_suppliers:
                    supplier_id = item.get(item_supplier['supplier'], '')
                    qty = item.get(item_supplier['qty'], 0)
                    rate = item.get(item_supplier['rate'], 0)
                    priority = item_supplier['priority']

                    if not math.isnan(supplier_id) and not math.isnan(stock_id):
                        item_supp_instance = PredictionItemSupplier.objects.get(
                            prediction_item__purchase_prediction__id=pur_pred_instance_id,
                            prediction_item__stock__id=int(stock_id),
                            supplier__id=int(supplier_id)
                        )
                        item_supp_instance.priority = priority
                        item_supp_instance.save(update_fields=['priority'])
            except:
                pass
        logger.info("Done!!!")
