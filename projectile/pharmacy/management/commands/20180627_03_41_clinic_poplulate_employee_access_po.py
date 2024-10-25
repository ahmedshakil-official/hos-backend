import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from pharmacy.models import EmployeeStorepointAccess

logger = logging.getLogger(__name__)


def populate_data():

    logger.info("Populating Person Organization in EmployeeStorepointAccess")

    items = EmployeeStorepointAccess.objects.all().exclude(organization__isnull=True)

    for item in tqdm(items):
        item.person_organization = item.employee.get_person_organization_for_employee(
            item.organization
        )
        item.save()


class Command(BaseCommand):
    '''
    This management script popluate all PersonOrganization data on person_organization field
    of EmployeeStorepointAccess model
    '''

    def handle(self, **options):
        populate_data()
