import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models.signals import pre_save
from common.enums import Status
from common.helpers import get_organization_by_input_id, get_storepoint_by_id
from pharmacy.models import StockAdjustment, StockIOLog, OrganizationWiseDiscardedProduct, Stock

from pharmacy.signals import (
    pre_save_stock_io_log,
    pre_save_stock
)
logger = logging.getLogger()


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("Fixing stock info")
        # getting organization from user input
        organization = get_organization_by_input_id()

        # select particular storepoint
        particular_storepoint = get_storepoint_by_id(organization)

        # finding discarded product of particular organization
        problamatic_products = OrganizationWiseDiscardedProduct.objects.filter(
            organization=organization,
        )

        # finding all the stock adjustment entry of given storepoint
        adjustments = StockAdjustment.objects.filter(
            status=Status.ACTIVE,
            organization=organization,
            store_point=particular_storepoint
        ).only(
            'id'
        )

        # fidning all stock io of related stock adjustment
        adjustment_stock_ios = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=organization,
            adjustment__in=adjustments
        ).select_related(
            'stock'
        )


        # travarsing through each discarded product
        for product in tqdm(problamatic_products):

            # finding invalid stock object
            invalid_stock = Stock.objects.filter(
                status=Status.ACTIVE,
                store_point=particular_storepoint,
                product=product.parent
            )

            if invalid_stock.exists():
                # finiding invalid stock_io if invalid stock exists
                problamtic_adjustment_stock_ios = adjustment_stock_ios.filter(
                    status=Status.ACTIVE,
                    stock__product=product.parent,
                )

                # finding valid stock object
                valid_stock = Stock.objects.filter(
                    status=Status.ACTIVE,
                    store_point=particular_storepoint,
                    product=product.product
                )

                if valid_stock.exists():

                    invalid_stock = invalid_stock.first()
                    valid_stock = valid_stock.first()

                    if problamtic_adjustment_stock_ios.exists():
                        # disconnect signal stock_io signal
                        pre_save.disconnect(pre_save_stock_io_log, sender=StockIOLog)


                        # replace all stock io of that belongs to invalid_product with valid product
                        for stock_io in problamtic_adjustment_stock_ios:
                            stock_io.stock = valid_stock
                            stock_io.rate = valid_stock.product.purchase_price
                            stock_io.save(update_fields=['stock', 'rate'])

                        # increase stock of valid product with stock of invalid product
                        valid_stock.stock = valid_stock.stock + invalid_stock.stock
                        valid_stock.save(update_fields=['stock'])

                        # re-connect stock_io signal
                        pre_save.connect(pre_save_stock_io_log, sender=StockIOLog)

                    # disconnect signal stock signal
                    pre_save.disconnect(pre_save_stock, sender=Stock)
                    # inactive invalid stock
                    invalid_stock.status = Status.INACTIVE
                    invalid_stock.save(update_fields=['status'])

                    # re-connect stock signal
                    pre_save.connect(pre_save_stock, sender=Stock)

                else:
                    logger.info("no stock exits for {} or {}".format(
                        product.product,
                        product.parent
                    ))
