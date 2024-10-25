import os
from django.core.management.base import BaseCommand

from common.helpers import populate_es_index
from common.enums import Status


class Command(BaseCommand):
    '''
    This management script will populate all Person Organization instances, where organization ID is 303
    '''

    def handle(self, **options):
        org_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        filters = {
            'status__in': [Status.ACTIVE, Status.DRAFT],
            'organization__id': org_id,

        }
        populate_es_index('core.models.PersonOrganization', filters, True)
