import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models import Sum, FloatField, F
from django.db.models.functions import Coalesce
from ecommerce.models import ShortReturnItem, ShortReturnLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("Fixing Short Return Item Log")
        start_date = "2021-10-29"
        short_return_items = ShortReturnItem.objects.filter(
            date__gt=start_date,
        )

        update_short_return_item = []
        for item in short_return_items:
            calculated_discount_total = ((item.quantity * item.rate) * item.discount_rate) / 100
            if calculated_discount_total != item.discount_total:
                item.discount_total = calculated_discount_total
                update_short_return_item.append(item)

        # Update short return item discount total
        ShortReturnItem.objects.bulk_update(
            objs=update_short_return_item,
            fields=['discount_total'],
            batch_size=100,
        )
        aggregated_short_return_logs = short_return_items.values('short_return_log').annotate(
            short_return_total=Coalesce(Sum(
                (F('quantity') *
                F('rate')) - F('discount_total'),
                output_field=FloatField()
            ), 0.00))

        update_short_return_log = []
        for item in tqdm(list(aggregated_short_return_logs)):
            instance = ShortReturnLog.objects.only('short_return_amount').get(pk=item['short_return_log'])
            instance.short_return_amount = item.get('short_return_total')
            round_discount = float(format(round(item.get('short_return_total')) - item.get('short_return_total'), '.3f'))
            instance.round_discount = round_discount
            update_short_return_log.append(instance)

        # Update short return item log instance
        ShortReturnLog.objects.bulk_update(
            objs=update_short_return_log,
            fields=['short_return_amount', 'round_discount'],
            batch_size=100,
        )
