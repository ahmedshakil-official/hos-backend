import logging
import datetime
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.utils import timezone

# from common.helpers import custom_elastic_rebuild
from pharmacy.models import Sales, Purchase

logger = logging.getLogger(__name__)

def populate_sales_data():

    logger.info("Populating Sales")
    sales = Sales.objects.filter()
    sales_update_count = 0
    for sale in tqdm(sales):
        # Sales.update()
        new_datetime = datetime.datetime.combine(sale.sale_date, sale.created_at.time())
        new_datetime = timezone.make_aware(new_datetime, timezone.get_current_timezone())
        Sales.objects.filter(pk=sale.id).update(sale_date=new_datetime)
        # custom_elastic_rebuild(
        #     'pharmacy.models.Sales', {'id': sale.id}
        # )
        sales_update_count += 1
    logger.info("{} Sales updated.".format(sales_update_count))


def populate_purchase_data():
    logger.info("Populating Purchases")
    purchases = Purchase.objects.filter()
    purchase_update_count = 0
    for purchase in tqdm(purchases):
        # Sales.update()
        new_datetime = datetime.datetime.combine(purchase.purchase_date, purchase.created_at.time())
        new_datetime = timezone.make_aware(new_datetime, timezone.get_current_timezone())
        Purchase.objects.filter(pk=purchase.id).update(purchase_date=new_datetime)
        # custom_elastic_rebuild(
        #     'pharmacy.models.Purchase', {'id': purchase.id}
        # )
        purchase_update_count += 1
    logger.info("{} Purchase updated.".format(purchase_update_count))


class Command(BaseCommand):
    '''
    This management script to Populate Product's Full Name
    '''
    def handle(self, **options):
        populate_sales_data()
        populate_purchase_data()
