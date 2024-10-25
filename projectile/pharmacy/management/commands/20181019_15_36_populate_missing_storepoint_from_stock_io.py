import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from pharmacy.models import Sales

logger = logging.getLogger('')


class Command(BaseCommand):
    def handle(self, **options):
        sales = Sales.objects.filter(
            store_point__isnull=True
        )
        for sale in tqdm(sales):
            try:
                sale.store_point = sale.stock_io_logs.all()[
                    :1][0].stock.store_point
                sale.save()
            except IntegrityError:
                pass
