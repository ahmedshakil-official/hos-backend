import json
import os
import logging
from projectile.settings import REPO_DIR
from django.db import IntegrityError
from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand
from pharmacy.models import Purchase, StockIOLog

logger = logging.getLogger(__name__)


def purchae_order_date():
    print "Collect Purchase order details"
    try:
        data = open(os.path.join(REPO_DIR, 'tmp/purchase-order.json'), 'r')
        json_data = json.load(data)
        for item in tqdm(json_data):
            try:
                stock_io_purchases = StockIOLog.objects.filter(
                    Q(purchase__id=item['purchase_order']))
                if stock_io_purchases.exists():
                    for stock_io in stock_io_purchases:
                        stock_io.date = item['date']
                        stock_io.save()
            except stock_io_purchases.DoesNotExist:
                logger.info("Stock IO purchase doesn't exist")

            try:
                purchase_id = Purchase.objects.get(id=item['purchase_order'])
                if purchase_id:
                    purchase_id.purchase_date = item['date']
                    purchase_id.save()
            except purchase_id.DoesNotExist:
                logger.info("Purchase doesn't exist")

    except (IntegrityError, IndexError, EOFError, IOError) as exception:
        logger.exception(exception)


class Command(BaseCommand):
    def handle(self, **options):
        purchae_order_date()
