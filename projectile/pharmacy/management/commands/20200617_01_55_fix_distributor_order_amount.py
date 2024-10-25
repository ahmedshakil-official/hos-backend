import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models.aggregates import Max

from common.enums import Status
from pharmacy.enums import DistributorOrderType, PurchaseType
from pharmacy.models import (
    Purchase,
    DistributorOrderGroup,
    StockIOLog
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        order_filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }
        order_groups = DistributorOrderGroup.objects.filter(
            status=Status.ACTIVE,
            order_type=DistributorOrderType.ORDER
        )
        for group in order_groups:
            sub_total = 0
            discount = 0
            group_round_discount = 0
            order_filters['distributor_order_group'] = group
            orders = Purchase.objects.filter(**order_filters)

            for order in orders:
                # get calculated amount of a specific order
                order_amount_data = order.get_amount()
                if order_amount_data:
                    discount_rate = 0
                    order_sub_total = order_amount_data.get('sub_total', 0)
                    order_discount_total = order_amount_data.get('total_discount', 0)
                    if order_discount_total and order_sub_total:
                        discount_rate = (order_discount_total * 100) / order_sub_total
                    sub_total += order_sub_total
                    discount += order_discount_total
                    grand_total = order_sub_total - order_discount_total
                    round_discount = round(round(grand_total) - grand_total, 2)
                    group_round_discount += round_discount
                    order_data = {
                        'amount': order_sub_total,
                        'discount': order_discount_total,
                        'discount_rate': discount_rate,
                        'grand_total': grand_total + round_discount,
                        'round_discount': round_discount
                    }
                    order.__dict__.update(**order_data)
                    order.save(update_fields=[*order_data])
            group.sub_total = sub_total
            group.discount = discount
            group.round_discount = group_round_discount
            group.save(update_fields=['sub_total', 'discount', 'round_discount',])
        logger.info("{} Order Updated.".format(order_groups.count()))
