import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.helpers import get_json_data_from_file, get_or_create_global_object

from pharmacy.models import (
    ProductForm, ProductManufacturingCompany,
    ProductGeneric, ProductGroup, ProductSubgroup,
    Product, Unit,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("IMPORTING PRODUCT")
        product = get_json_data_from_file('tmp/all_medicine_data.json')

        group = get_or_create_global_object(ProductGroup, {'name': 'Medicine'})
        failed = 0
        for item in tqdm(product):
            try:
                factor = float(item['factor'])
                price = float(item['per_unit'])
            except (ValueError, TypeError):

                factor = 0.0
                price = 0.0

            form = get_or_create_global_object(
                ProductForm, {'name': item['form']})

            company = get_or_create_global_object(
                ProductManufacturingCompany, {'name': item['manufacturer']}
            )

            generic = get_or_create_global_object(
                ProductGeneric, {'name': item['generic_name']}
            )

            subgroup = get_or_create_global_object(
                ProductSubgroup, {
                    'name': item['subgroup'], 'product_group':  group}
            )

            punit = get_or_create_global_object(
                Unit, {'name': item['primary_unit']})

            sunit = get_or_create_global_object(Unit, {'name': item['sunit']})

            data = {
                'name': item['brand_name'],
                'form': form,
                'subgroup': subgroup,
                'manufacturing_company': company,
                'generic': generic,
                'primary_unit': punit,
                'secondary_unit': sunit,
                'conversion_factor': factor,
                'description': item['drug_for'],
                'trading_price': price,
                'purchase_price': price
            }

            if form is not None and company is not None and generic is not None and subgroup \
             is not None and punit is not None and sunit is not None:
                product = get_or_create_global_object(Product, data)
                if product is None:
                    failed = failed + 1
                    logger.error("failed to import {}".format(
                        item['brand_name']))
            else:
                failed = failed + 1
                logger.error("failed to import {}".format(item['brand_name']))

        logger.info("total product failed to import {} products".format(failed))
