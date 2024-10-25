import logging
import datetime
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.utils import timezone

from common.helpers import get_csv_data_from_temp_file
from pharmacy.models import Sales, Purchase

logger = logging.getLogger(__name__)

def populate_sales_data():

    logger.info("Populating Sales")
    sales_failed = []
    data = get_csv_data_from_temp_file('tmp/sales_info2.csv')
    for item in tqdm(data):
        try:
            sale = Sales.objects.get(pk=item['sales_id'])
            sale_date = sale.stock_io_logs.values('date',).order_by('id').first()['date']
            new_datetime = datetime.datetime.combine(sale_date, sale.created_at.time())
            new_datetime = timezone.make_aware(new_datetime, timezone.utc)
            Sales.objects.filter(pk=item['sales_id']).update(sale_date=new_datetime)
        except:
            sales_failed.append(item['sales_id'])
    logger.info("{} Sales Failed to update".format(sales_failed))


def populate_purchase_data():
    logger.info("Populating Purchases")
    purchase_failed = []
    data = get_csv_data_from_temp_file('tmp/purchase_info2.csv')
    for item in tqdm(data):
        try:
            purchase = Purchase.objects.get(pk=item['purchase_id'])
            purchase_date = purchase.stock_io_logs.values('date',).order_by('id').first()['date']
            new_datetime = datetime.datetime.combine(purchase_date, purchase.created_at.time())
            new_datetime = timezone.make_aware(new_datetime, timezone.utc)
            Purchase.objects.filter(pk=item['purchase_id']).update(purchase_date=new_datetime)
        except:
            purchase_failed.append(item['purchase_id'])
    logger.info("{} Purchases Failed to update".format(purchase_failed))


class Command(BaseCommand):
    '''
    This management script to Fix incorrect time zone of Sales and Purchase
    '''
    def handle(self, **options):
        populate_sales_data()
        populate_purchase_data()
