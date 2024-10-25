import logging

from tqdm import tqdm
from datetime import datetime
from pytz import timezone
from django.db.models import Sum
from django.core.management.base import BaseCommand
from pharmacy.models import Purchase, DistributorOrderGroup
from pharmacy.enums import DistributorOrderType
from pharmacy.utils import get_additional_discount_data

logger = logging.getLogger(__name__)


def apply_additional_discount():
    logger.info(f"Applying additional discount of all orders after 2021-11-09 8:59 AM")
    order_time_end = datetime.now(
        timezone('Asia/Dhaka')
    ).replace(
        year=2021,
        month=11,
        day=9,
        hour=8,
        minute=59,
        second=59,
        microsecond=0
    )

    order_groups = DistributorOrderGroup.objects.filter(
        order_type=DistributorOrderType.ORDER,
        order_groups__purchase_date__gt=order_time_end,
    ).values_list('group_id', flat=True).distinct()

    for group in order_groups:
        orders = Purchase.objects.filter(
            purchase_date__gt=order_time_end,
            additional_discount__lte=0,
            distributor_order_group__group_id=group
        ).only(
            'purchase_date',
            'organization__offer_rules',
            'is_queueing_order',
        ).annotate(
            _grand_total=Sum('amount') - Sum('discount') + Sum('round_discount')
        )
        group_grand_total = orders.aggregate(
            group_grand_total=Sum('amount') - Sum('discount') + Sum('round_discount')
        ).get('group_grand_total', 0)

        for order in orders:
            additional_discount_data = get_additional_discount_data(
                group_grand_total,
                order.is_queueing_order,
                order,
                order._grand_total
            )
            if additional_discount_data.get('discount', 0) > 0:
                order.apply_additional_discount(
                    **additional_discount_data
                )
    logger.info("Done!!!")


class Command(BaseCommand):
    def handle(self, **options):
        apply_additional_discount()
