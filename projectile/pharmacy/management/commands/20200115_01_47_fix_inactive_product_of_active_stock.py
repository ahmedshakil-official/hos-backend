import logging
from tqdm import tqdm
from common.helpers import (
    get_organization_by_input_id,
    get_storepoint_by_id,
)
from django.core.management.base import BaseCommand
from pharmacy.models import Product, OrganizationWiseDiscardedProduct, Stock
from pharmacy.helpers import stop_stock_signal, start_stock_signal
from common.enums import Status, DiscardType
from core.enums import OrganizationType
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        '''
        This script find all the stock which are active but associated product is in OrganizationWiseDiscardedProduct as parent
        we will replace the product of stock with product of particular OrganizationWiseDiscardedProduct
        '''
        # taking input of an organization
        organization_instance = get_organization_by_input_id(OrganizationType.PHARMACY)
        discarded_product_list = OrganizationWiseDiscardedProduct.objects.filter(
            organization=organization_instance,
            status=Status.ACTIVE,
            entry_type=DiscardType.MERGE,
            parent__status=Status.INACTIVE
        ).values_list('parent__id', flat=True)

        stocks = Stock.objects.filter(
            organization=organization_instance,
            status=Status.ACTIVE,
            product__status=Status.INACTIVE,
            product__id__in=discarded_product_list
        )

        for stock in tqdm(stocks):
            correct_product = OrganizationWiseDiscardedProduct.objects.filter(
                organization=organization_instance,
                status=Status.ACTIVE,
                parent=stock.product,
                entry_type=DiscardType.MERGE
            ).first().product
            if correct_product:
                stop_stock_signal()
                stock.product = correct_product
                stock.save(update_fields=['product'])
                start_stock_signal()
