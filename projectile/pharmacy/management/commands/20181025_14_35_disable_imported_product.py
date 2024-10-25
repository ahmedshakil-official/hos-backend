import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.helpers import get_json_data_from_file, get_global_active_record
from common.enums import Status

from pharmacy.models import (
    ProductManufacturingCompany,
    Product,
    StockIOLog
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):

        producers = get_json_data_from_file(
            'tmp/imported_product_manufacturer.json')

        for producer in tqdm(producers):
            products = None

            company = get_global_active_record(
                ProductManufacturingCompany, {'name': producer['producer']}
            )

            if company:
                products = get_global_active_record(
                    Product, {'manufacturing_company': company}, False
                )

            if products:
                for product in products:
                    stock_info = StockIOLog.objects.filter(
                        stock__product=product
                    )
                    if stock_info.exists():
                        logger.info("failed to disable {}".format(product))
                    else:
                        product.status = Status.DRAFT
                        product.save()
