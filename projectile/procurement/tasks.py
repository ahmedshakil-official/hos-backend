# -*- coding: ascii -*-
from __future__ import absolute_import, unicode_literals

import logging
import math
import time
from datetime import datetime
import pandas as pd
import re, difflib
from validator_collection import checkers

from projectile.celery import app
from common.enums import Status
from core.models import ScriptFileStorage, PersonOrganization

from pharmacy.models import Stock
from pharmacy.helpers import get_product_short_name
from pharmacy.tasks import populate_stock_supplier_avg_rate_cache

from .models import PurchasePrediction, PredictionItem, PredictionItemSupplier
from .enums import RecommendationPriority

logger = logging.getLogger(__name__)

def get_value_or_zero(value=0):
    if not math.isnan(value):
        return value
    return 0

@app.task
def create_purchase_prediction_from_file_lazy(file_name, file_instance_pk, lower_limit, upper_limit, organization_id):
    stock_file = ScriptFileStorage.objects.only(
        'content', 'entry_by_id', 'purpose',
    ).get(pk=file_instance_pk)
    stock_df =  pd.read_excel(stock_file.content)
    data_df = stock_df[lower_limit:upper_limit]
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

    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    DATE_FORMAT = '%Y-%m-%d'
    _datetime_now = datetime.strptime(
        time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
    _date_now = datetime.strptime(
        time.strftime(DATE_FORMAT, time.localtime()), DATE_FORMAT).date()

    purchase_prediction, _ = PurchasePrediction.objects.get_or_create(
        defaults={'date': _datetime_now, 'is_locked': False},
        prediction_file_id=file_instance_pk,
        organization_id=organization_id,
        entry_by_id=stock_file.entry_by_id,
        label=stock_file.purpose,
    )

    for index, item in data_df.iterrows():
        try:
            stock_id = item.get('ID', '')
            stock = Stock.objects.get(pk=stock_id)
            product_full_name = get_product_short_name(stock.product)
            company_name = stock.product.manufacturing_company.name
            employee_id = item.get('EMP_ID', '')
            assign_to = None
            if not math.isnan(employee_id):
                is_employee_exist_in_db = PersonOrganization.objects.only('id').filter(pk=employee_id)
                if is_employee_exist_in_db.exists():
                    assign_to = employee_id

            if not math.isnan(stock_id):
                # populate_stock_supplier_avg_rate_cache.delay(int(stock_id))
                check_existing = PredictionItem.objects.filter(
                    status=Status.ACTIVE,
                    stock__id=stock_id,
                    purchase_prediction=purchase_prediction,
                    product_name=product_full_name,
                    company_name=company_name,
                    index=index,
                )
                if not check_existing.exists():
                    data = {
                        'date': _date_now,
                        'stock_id': stock_id,
                        'mrp': get_value_or_zero(item.get('MRP', 0)),
                        'sale_price': get_value_or_zero(item.get('SP', 0)),
                        'avg_purchase_rate': get_value_or_zero(item.get('AVG', 0)),
                        'lowest_purchase_rate': get_value_or_zero(item.get('L_RATE', 0)),
                        'highest_purchase_rate': get_value_or_zero(item.get('H_RATE', 0)),
                        'margin': 0 if not get_value_or_zero(item.get('AVG', 0)) else (get_value_or_zero(item.get('SP', 0)) - get_value_or_zero(item.get('AVG', 0))) * 100 / get_value_or_zero(item.get('AVG', 0)),
                        'product_visibility_in_catelog': item.get('STATUS', ''),
                        'sold_quantity': get_value_or_zero(item.get('SELL', 0)),
                        'purchase_quantity': get_value_or_zero(item.get('PUR', 0)),
                        'short_quantity': get_value_or_zero(item.get('SHORT', 0)),
                        'return_quantity': get_value_or_zero(item.get('RET', 0)),
                        'new_stock': get_value_or_zero(item.get('NSTOCK', 0)),
                        'prediction': get_value_or_zero(item.get('PRED', 0)),
                        'new_order': get_value_or_zero(item.get('NORDER', 0)),
                        'suggested_purchase_quantity': get_value_or_zero(item.get('D3', 0)),
                        'suggested_min_purchase_quantity': get_value_or_zero(item.get('D1', 0)),
                        'purchase_prediction': purchase_prediction,
                        'organization_id': organization_id,
                        'entry_by_id': stock_file.entry_by_id,
                        'product_name': product_full_name,
                        'company_name': company_name,
                        'real_avg': get_value_or_zero(item.get('RAVG', 0)),
                        'assign_to_id': assign_to,
                        'team': item.get('TEAM', ''),
                        'sale_avg_3d': get_value_or_zero(item.get('3D', 0)),
                        'worst_rate': get_value_or_zero(item.get('WRATE', 0)),
                        'index': index
                    }
                    if data.get('suggested_min_purchase_quantity', 0) > 0:
                        data['has_min_purchase_quantity'] = True

                    prediction_item = PredictionItem.objects.create(**data)
                    # Create item suppliers
                    for item_supplier in pred_item_suppliers:
                        supplier_id = item.get(item_supplier['supplier'], '')
                        qty = item.get(item_supplier['qty'], 0)
                        rate = item.get(item_supplier['rate'], 0)
                        priority = item_supplier['priority']

                        if not math.isnan(supplier_id):
                            is_supplier_exist_in_db = PersonOrganization.objects.only('id').filter(pk=supplier_id)
                            if is_supplier_exist_in_db.exists():
                                PredictionItemSupplier.objects.create(
                                    prediction_item=prediction_item,
                                    organization_id=organization_id,
                                    entry_by_id=stock_file.entry_by_id,
                                    supplier_id=int(supplier_id),
                                    rate=get_value_or_zero(rate),
                                    quantity=get_value_or_zero(qty),
                                    priority=priority
                                )
        except:
            pass

@app.task
def update_purchase_order_qty_for_pred_item(pred_item_id):
    try:
        pred_item = PredictionItem.objects.only('id', 'purchase_order',).get(pk=pred_item_id)
        total_purchase_order_qty = pred_item.get_total_purchase_order_qty()
        if total_purchase_order_qty != float(pred_item.purchase_order):
            pred_item.purchase_order = total_purchase_order_qty
            pred_item.save(update_fields=['purchase_order', ])
    except:
        pass