import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q

from common.enums import (
    Status, PublishStatus
)

from core.models import OrganizationSetting

from pharmacy.models import (
    Stock,
    Product,
    StockIOLog,
    OrganizationWiseDiscardedProduct
)

from pharmacy.enums import GlobalProductCategory

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        # Find all organization with GPB
        organizations = OrganizationSetting.objects.filter(
            global_product_category=GlobalProductCategory.GPB,
        ).values_list('organization__id', flat=True)

        for organization in tqdm(organizations):
            # Find the discardable products
            discarded_global_product = OrganizationWiseDiscardedProduct.objects.filter(
                organization=organization,
                parent__global_category=GlobalProductCategory.GPB,
                parent__is_global=PublishStatus.INITIALLY_GLOBAL
            ).values_list('parent_id', flat=True).distinct()

            # Fixable stock(stocks with no IO operation)
            stocks_replaceable = Stock.objects.filter(
                organization=organization,
                status=Status.ACTIVE,
            ).filter(
                product__id__in=discarded_global_product
            ).filter(~Q(
                id__in=StockIOLog.objects.filter(
                    organization=organization
                ).values_list('stock_id', flat=True).distinct()
            ))

            for stock_replaceable in stocks_replaceable:
                problematic_stock = stock_replaceable

                # Find possible correct product having at least one Stock
                possible_correct_product = OrganizationWiseDiscardedProduct.objects.filter(
                    parent=problematic_stock.product,
                    product__status=Status.ACTIVE,
                    product__id__in=Stock.objects.filter(
                        status=Status.ACTIVE,
                        organization=organization,
                        store_point=problematic_stock.store_point
                    ).values_list('product_id', flat=True)
                ).only('product').first()

                if possible_correct_product is None:
                    logger.info('not possible to replace')
                else:
                    # Find correct stock if the stock is fixable
                    correct_stock = Stock.objects.filter(
                        organization=organization,
                        store_point=problematic_stock.store_point,
                        product=possible_correct_product.product,
                        status=Status.ACTIVE
                    ).first()

                    if correct_stock is not None:

                        logger.info('replacing \n{} \nwith \n{}\n\n----------------------------'.format(
                            problematic_stock, correct_stock
                        ))

                        # Make the problematic stock inactive if we found a correct stock for this
                        problematic_stock.status = Status.INACTIVE
                        problematic_stock.save(update_fields=['status'])
