import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models.aggregates import Max

from pharmacy.models import (
    Stock,
    StockIOLog
)

from common.enums import Status
from common.utils import get_ratio


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):

        # queryset return last purchse stock_io_log_id , stock_id
        storepoint_wise_stock_ios = StockIOLog.objects.values(
            'stock'
        ).filter(
            status=Status.ACTIVE,
            purchase__isnull=False
        ).annotate(
            stock_io_id=Max('id')
        ).order_by('stock')

        for item in tqdm(storepoint_wise_stock_ios):
            # get obj of corresponsding stock io log id
            stock_io_log = StockIOLog.objects.get(
                pk=item['stock_io_id']
            )

            purchase_subtotal, additional_price = \
                stock_io_log.get_purchase_price_info()

            stock = Stock.objects.get(
                pk=item['stock']
            )

            # setting calculated_price_organization_wise

            if purchase_subtotal is not None and additional_price is not None:

                trade_price = stock_io_log.get_trade_price()

                ratio_of_additional_cost = get_ratio(
                    purchase_subtotal,
                    trade_price * stock_io_log.quantity
                )

                vat_per_item = stock_io_log.vat_total / stock_io_log.quantity
                tax_per_item = stock_io_log.tax_total / stock_io_log.quantity
                discount_per_item = \
                    stock_io_log.discount_total / stock_io_log.quantity

                new_price = trade_price + vat_per_item + tax_per_item + \
                    (((additional_price/100)*ratio_of_additional_cost) /
                        stock_io_log.quantity) \
                    - discount_per_item

                stock.calculated_price = round(new_price, 4)
                stock.calculated_price_organization_wise = round(new_price, 4)

                stock.save()
