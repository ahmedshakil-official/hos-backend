import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from core.models import PersonOrganization
from core.utils import getCountryCode


logger = logging.getLogger(__name__)


def populate_country_code():

    logger.info("UPDATING COUNTRY CODE")

    person_list = PersonOrganization.objects.filter(country__isnull=False)
    for person in tqdm(person_list):
        country_code = getCountryCode(person.country)
        person.country_code = country_code['code']

        person.save()


class Command(BaseCommand):
    def handle(self, **options):
        populate_country_code()
