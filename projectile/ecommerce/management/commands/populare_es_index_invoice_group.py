import os
from django.core.management.base import BaseCommand

from common.helpers import populate_es_index


class Command(BaseCommand):
    '''
    This management script will populate all order and invoice group the date
    '''

    def handle(self, **options):
        delivery_date = "2022-08-27"
        filters = {
            "purchase_date__gte": delivery_date
        }
        populate_es_index('pharmacy.models.Purchase', filters, True)

        invoice_groups_filters = {
            "delivery_date": delivery_date
        }
        populate_es_index('ecommerce.models.OrderInvoiceGroup', invoice_groups_filters, True)
