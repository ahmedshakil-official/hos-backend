import logging
from itertools import chain, repeat
import pandas as pd
from tqdm import tqdm
import math, os
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from common.enums import Status
from core.models import ScriptFileStorage
from pharmacy.models import Stock
from pharmacy.helpers import get_product_short_name
from procurement.models import PurchasePrediction, PredictionItem, PredictionItemSupplier
from procurement.enums import RecommendationPriority

logger = logging.getLogger(__name__)


def get_value_or_zero(value=0):
    if not math.isnan(value):
        return value
    return 0

def is_valid_prediction_file(file):

    purchase_prediction_columns = [
        'ID',
        'MRP',
        'SP',
        'AVG',
        'L_RATE',
        'H_RATE',
        'KIND',
        'STATUS',
        'OSTOCK',
        'SELL',
        'PUR',
        'SHORT',
        'RET',
        'NSTOCK',
        'PRED',
        'NORDER',
        'D3',
        'SUPPLIER_S1',
        'QTY_S1',
        'RATE_S1',
        'SUPPLIER_S2',
        'QTY_S2',
        'RATE_S2',
        'SUPPLIER_S3',
        'QTY_S3',
        'RATE_S3'
    ]

    stock_df =  pd.read_excel(file.content)
    columns_from_file = stock_df.columns.to_list()
    missing_columns = list(set(purchase_prediction_columns) - set(columns_from_file))
    if not missing_columns:
        return True
    return False

def populate_data(file, organization_id):
    stock_df =  pd.read_excel(file.content)

    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    DATE_FORMAT = '%Y-%m-%d'
    _datetime_now = datetime.strptime(
        time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
    _date_now = datetime.strptime(
        time.strftime(DATE_FORMAT, time.localtime()), DATE_FORMAT).date()

    purchase_prediction, _ = PurchasePrediction.objects.get_or_create(
        defaults={'date': _datetime_now},
        prediction_file_id=file.id,
        organization_id=organization_id,
        entry_by_id=file.entry_by_id,
        # label=file.purpose,
    )
    new_instance_count = 0

    for index, item in tqdm(stock_df.iterrows()):
        stock_id = item.get('ID', '')
        stock = Stock.objects.get(pk=stock_id)
        product_full_name = get_product_short_name(stock.product)
        company_name = stock.product.manufacturing_company.name

        if not math.isnan(stock_id):
            check_existing = PredictionItem.objects.filter(
                status=Status.ACTIVE,
                stock__id=stock_id,
                purchase_prediction=purchase_prediction,
                product_name=product_full_name,
                company_name=company_name
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
                    'purchase_prediction': purchase_prediction,
                    'organization_id': organization_id,
                    'entry_by_id': file.entry_by_id,
                    'product_name': product_full_name,
                    'company_name': company_name,
                }

                prediction_item = PredictionItem.objects.create(**data)
                supplier_s1 = item.get('SUPPLIER_S1', '')
                supplier_s2 = item.get('SUPPLIER_S2', '')
                supplier_s3 = item.get('SUPPLIER_S3', '')
                new_instance_count += 1

                if not math.isnan(supplier_s1):
                    PredictionItemSupplier.objects.create(
                        prediction_item=prediction_item,
                        organization_id=organization_id,
                        entry_by_id=file.entry_by_id,
                        supplier_id=int(supplier_s1),
                        rate=get_value_or_zero(item.get('RATE_S1', 0)),
                        quantity=get_value_or_zero(item.get('QTY_S1', 0)),
                        priority=RecommendationPriority.HIGH
                    )

                if not math.isnan(supplier_s2):
                    PredictionItemSupplier.objects.create(
                        prediction_item=prediction_item,
                        organization_id=organization_id,
                        entry_by_id=file.entry_by_id,
                        supplier_id=int(supplier_s2),
                        rate=get_value_or_zero(item.get('RATE_S2', 0)),
                        quantity=get_value_or_zero(item.get('QTY_S2', 0)),
                        priority=RecommendationPriority.MEDIUM
                    )

                if not math.isnan(supplier_s3):
                    PredictionItemSupplier.objects.create(
                        prediction_item=prediction_item,
                        organization_id=organization_id,
                        entry_by_id=file.entry_by_id,
                        supplier_id=int(supplier_s3),
                        rate=get_value_or_zero(item.get('RATE_S3', 0)),
                        quantity=get_value_or_zero(item.get('QTY_S3', 0)),
                        priority=RecommendationPriority.LOW
                    )
    logger.info(f"Total {new_instance_count} new instance created.")


class Command(BaseCommand):
    '''
    This management script will fix missing entry for provided prediction_file
    '''

    def handle(self, **options):
        organization_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        prompts = chain(["Enter prediction file id: "], repeat("Not a valid id! Try again: "))
        replies = map(input, prompts)
        valid_response = next(filter(str.isdigit, replies))
        try:
            pred_file = ScriptFileStorage.objects.only(
                'content', 'entry_by_id', 'purpose',
            ).get(pk=valid_response)
        except Exception as exp:
            pred_file = None
            logger.error(str(exp))
        if is_valid_prediction_file(pred_file):
            populate_data(pred_file, organization_id)
        else:
            logger.error("Invalid file")
