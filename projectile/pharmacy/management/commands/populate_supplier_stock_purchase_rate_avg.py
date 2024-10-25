import logging, os
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.cache import cache
from common.cache_keys import PERSON_ORG_SUPPLIER_STOCK_RATE_AVG
from common.enums import Status
from pharmacy.helpers import get_average_purchase_price
from pharmacy.models import Stock

from core.models import Organization


logger = logging.getLogger(__name__)

def populate_supplier_stock_purchase_rate_avg_cache():
    logger.info("POPULATING SUPPLIER STOCK PURCHASE RATE AVG CACHE")
    base_cache_key = PERSON_ORG_SUPPLIER_STOCK_RATE_AVG
    org_id =  os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    org = Organization.objects.only('id').get(pk=org_id)
    supplier_alias_list = org.get_po_supplier_alias_list()
    stock_id_list = Stock.objects.filter(
        status=Status.ACTIVE,
        organization__id=org_id,
        product__organization__id=org_id
    ).values_list('id', flat=True)
    timeout = 43200
    for stock_id in tqdm(list(stock_id_list)):
        for supplier_alias in supplier_alias_list:
            supplier_avg_rate = get_average_purchase_price(
                stock_id=stock_id,
                person_organization_supplier_alias=supplier_alias
            )
            cache_key = f"{base_cache_key}_{stock_id}_{supplier_alias}"
            cache.set(cache_key, supplier_avg_rate, timeout)

    message = f"Total {stock_id_list.count()} and {len(supplier_alias_list)} Supplier data populated"
    logger.info(message)

class Command(BaseCommand):
    def handle(self, **options):
        populate_supplier_stock_purchase_rate_avg_cache()
