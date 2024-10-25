import os
from django.core.management.base import BaseCommand

from common.helpers import populate_es_index
from common.enums import Status
from pharmacy.enums import PurchaseType


class Command(BaseCommand):
    '''
    This management script will populate all purchase of HealthOS
    '''

    def handle(self, **options):
        org_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        org_id = org_id if org_id else 303
        filters = {
            'status': Status.ACTIVE,
            'organization__id': org_id,
            'purchase_type': PurchaseType.PURCHASE

        }
        populate_es_index('pharmacy.models.Purchase', filters, True)
