import logging
from tqdm import tqdm
from datetime import date

from django.core.cache import cache
from django.core.management.base import BaseCommand

from common.enums import Status, PublishStatus
from common.helpers import get_csv_data_from_temp_file
from pharmacy.models import (
    Product,
    ProductManufacturingCompany,
    Stock,
)

logger = logging.getLogger(__name__)


def update_manufacturing_company():

    logger.info("Fixing Duplicate Manufacturing Company")
    failed_company = []
    update_count = 0
    stock_list = []
    data = get_csv_data_from_temp_file('tmp/company_list.csv')
    for item in tqdm(data):
        try:
            replaced_manufacturer = ProductManufacturingCompany.objects.get(
                pk=item['replace_with'])
            if replaced_manufacturer.is_global in [
                    PublishStatus.INITIALLY_GLOBAL,
                    PublishStatus.WAS_PRIVATE_NOW_GLOBAL]:
                products = Product.objects.filter(
                    manufacturing_company__id=item['id'])
                # store stock id
                stock_list += list(Stock.objects.filter(
                    product__in=products,
                    status=Status.ACTIVE
                ).values_list('id', flat=True))
                products_count = products.count()
                # update products manufacturing company
                products.update(manufacturing_company=replaced_manufacturer)
                update_count += products_count
                try:
                    deleted_company = ProductManufacturingCompany.objects.get(pk=item['id'])
                    deleted_company.status = Status.INACTIVE
                    deleted_company.description = "Making Inactive on {} for fixing duplicate".format(
                        date.today()
                    )
                    deleted_company.save(update_fields=['status', 'description'])
                except:
                    logger.error("Failed to delete Company of ID: {}").format(item['id'])

        except Exception as exception:
            failed_company.append({
                item['id']: item['company'],
                'Error': exception
            })

    if stock_list:
        logger.info("Expiring cache..........")
        # generate cache key from stock id
        stock_key_list = ['stock_instance_{}'.format(
            str(stock_id).zfill(12)) for stock_id in stock_list]
        # remove all cache key
        cache.delete_many(stock_key_list)
        logger.info("Done.....")

    logger.info(
        "{} Products updated of {} manufacturing company".format(
            update_count, len(data)))
    logger.info(
        "{} Manufacturing comapany failed to update".format(failed_company))


class Command(BaseCommand):
    '''
    This management script to fix duplicate manufacturing company
    '''
    def handle(self, **options):
        update_manufacturing_company()
