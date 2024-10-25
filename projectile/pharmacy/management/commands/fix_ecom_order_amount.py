import logging
from tqdm import tqdm
from datetime import datetime, timedelta
from pytz import timezone

from django.core.management.base import BaseCommand
from django.core.cache import cache

from common.enums import Status
from common.helpers import custom_elastic_rebuild

from core.models import  Organization

from pharmacy.models import Purchase,DistributorOrderGroup
from pharmacy.enums import PurchaseType, DistributorOrderType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    Fixing stock quantity calculating related ioLogs for HealthOS E-Commerce
    '''

    def handle(self, **options):

        try:
            healthos_org_instance = Organization.objects.only('id').get(
                pk=303
            )
        except Organization.DoesNotExist:
            healthos_org_instance = Organization.objects.only('id').get(
                pk=41
            )

        localtz = timezone('Asia/Dhaka')
        date_format = '%Y-%m-%d %H:%M:%S'
        today = datetime.now(timezone('Asia/Dhaka'))
        last_order_date = today - timedelta(days=15)

        order_groups = DistributorOrderGroup.objects.filter(
            status=Status.ACTIVE,
            order_type=DistributorOrderType.ORDER,
            created_at__gte=last_order_date
        ).exclude(
            order_type=DistributorOrderType.CART
        )

        update_count = 0
        for order_group in tqdm(order_groups):
            sub_total = 0
            discount = 0
            group_round_discount = 0
            orders = order_group.order_groups.filter(
                status=Status.DISTRIBUTOR_ORDER,
                distributor=healthos_org_instance,
                purchase_type=PurchaseType.VENDOR_ORDER,
                distributor_order_type= DistributorOrderType.ORDER,
                stock_io_logs__status=Status.DISTRIBUTOR_ORDER
            ).only(
                'id',
                'amount',
                'discount_rate',
                'grand_total',
                'round_discount',
            ).distinct()
            for order in orders:
                # get calculated amount of a specific order
                order_amount_data = order.get_amount()
                if order_amount_data:
                    order_sub_total = order_amount_data.get('sub_total', 0)
                    order_discount_total = order_amount_data.get('total_discount', 0)
                    discount_rate = (order_discount_total * 100) / order_sub_total
                    sub_total += order_sub_total + order.additional_cost
                    discount += order_discount_total + order.additional_discount
                    grand_total = order_sub_total - order_discount_total + order.additional_cost - order.additional_discount
                    round_discount = round(round(grand_total) - grand_total, 2)
                    group_round_discount += round_discount
                    order_data = {
                        'amount': float(format(order_sub_total, '0.3f')),
                        'discount': float(format(order_discount_total, '0.3f')),
                        'discount_rate': float(format(discount_rate, '0.3f')),
                        'grand_total': float(format(grand_total + round_discount, '0.3f')),
                        'round_discount': float(format(round_discount, '0.3f')),
                    }
                    if abs(order.grand_total - grand_total) > 1:
                        logger.info(
                            f"Updating Order amount for order id {order.id}: PREV AMOUNT - {order.grand_total} CALCULATED AMOUNT - {order_data.get('grand_total')}"
                        )
                        update_count += 1
                        order.__dict__.update(**order_data)
                        order.save(update_fields=[*order_data])
            order_group.sub_total = sub_total
            order_group.discount = discount
            order_group.round_discount = group_round_discount
            order_group.save(update_fields=['sub_total', 'discount', 'round_discount',])
            custom_elastic_rebuild(
                'pharmacy.models.Purchase', {'id__in': list(orders.values_list('pk', flat=True))})


        logger.info(
            '-------------------------------------------------------------------')

        report = """
        total update count = {}"""

        logger.info(report.format(
            update_count,
        ))
