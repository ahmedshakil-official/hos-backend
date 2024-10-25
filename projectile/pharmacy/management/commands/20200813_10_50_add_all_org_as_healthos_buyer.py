import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from common.enums import Status
from core.enums import OrganizationType
from core.models import Organization

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        '''
        This script will add all organization as HealthOS buyer
        '''
        logger.info("Add all organization as HealthOS Buyer")
        organizations = Organization.objects.filter(
            status=Status.ACTIVE,
        ).exclude(
            type=OrganizationType.DISTRIBUTOR
        ).only('id', 'name', 'primary_mobile').order_by('id')

        for organization in tqdm(organizations):
            organization.add_as_distributor_buyer()
        logger.info("Done!!")
