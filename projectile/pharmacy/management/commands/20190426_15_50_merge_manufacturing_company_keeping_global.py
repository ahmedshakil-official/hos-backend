import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from pharmacy.models import Product, ProductManufacturingCompany

from common.helpers import (
    get_organization_by_input_id,
    get_manufacturing_companies_by_input_id,
    custom_elastic_rebuild
)

from common.enums import Status

logger = logging.getLogger()

def update_products_of_replaced_company(organization, old, new):
    products = Product.objects.filter(
        organization=organization,
        manufacturing_company=old,
    )
    for product in tqdm(products):
        Product.objects.filter(pk=product.id).update(manufacturing_company_id=new)
        custom_elastic_rebuild('pharmacy.models.Product', {'id': product.id})
    logger.info("All Product Updated with Company ID: #{}".format(new))


class Command(BaseCommand):
    '''
    This management script will take input of an organization, accounts an employee and two date
    and move all transaction to another account
    '''

    def handle(self, **options):
        # logger.info("Populating Transaction Group")
        organization_instance = get_organization_by_input_id()
        companies = get_manufacturing_companies_by_input_id(
            organization_instance,
            'Select Company/Companies (ID) (separate by a whitespace) : \n',
            ProductManufacturingCompany
        )
        update_count = 0
        for company in companies:
            inactive_company = ProductManufacturingCompany.objects.get(pk=company['old'])
            inactive_company.status = Status.INACTIVE
            inactive_company.save(update_fields=['status'])
            update_products_of_replaced_company(
                organization_instance, company['old'], company['new']
            )
            update_count += 1
        logger.info("***********************************************************")
        logger.info("{} Company Replaced".format(update_count))
        logger.info("***********************************************************")
