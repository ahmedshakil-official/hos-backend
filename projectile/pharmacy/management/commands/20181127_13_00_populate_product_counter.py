import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models import Count

from pharmacy.models import (
    StockIOLog,
    Stock,
    Product,
)

logger = logging.getLogger(__name__)


def get_product_count(argument_values, argument_count):
    return StockIOLog.objects.all(
    ).values(
        *argument_values
    ).annotate(
        total=Count(argument_count)
    ).order_by('-total')


class Command(BaseCommand):

    def handle(self, **options):

        # Transaction.objects.all().values('actor').annotate(total=Count('actor')).order_by('total')

        local_count = get_product_count(['stock__id'], 'stock__id')
        organization_count = get_product_count(
            ['stock__product', 'organization'], 'stock__product__id')
        global_count = get_product_count(
            ['stock__product'], 'stock__product__id')

        logger.info("POPULATING GLOBAL COUNT")
        for item in tqdm(global_count):
            Stock.objects.filter(
                product__id=item['stock__product']
            ).update(
                global_count=item['total']
            )

        logger.info("POPULATING ORGANIZATION WISE COUNT")
        for item in tqdm(organization_count):
            Stock.objects.filter(
                product__id=item['stock__product'],
                organization__id=item['organization']
            ).update(
                organizationwise_count=item['total']
            )

        logger.info("POPULATING LOCAL COUNT")
        for item in tqdm(local_count):
            Stock.objects.filter(
                id=item['stock__id']
            ).update(
                local_count=item['total']
            )
