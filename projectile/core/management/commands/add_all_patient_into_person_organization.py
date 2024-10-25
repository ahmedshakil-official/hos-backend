import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from core.models import Person, PersonOrganization
logger = logging.getLogger(__name__)


def add_person_into_person_organization():
    logger.info("ADD PATIENT INTO PERSON ORGANIZATION....")
    persons = Person.objects.all()

    patient_count = 0
    for person in tqdm(persons):
        try:
            obj, created = PersonOrganization.objects.update_or_create(
                person=person,
                organization=person.organization,
                defaults={'balance': person.balance, 'status': person.status},
            )
            patient_count += 1

        except (AttributeError, IndexError, EOFError, IOError) as exception:
            logger.exception(exception)

    logger.info("{} Patient added into person organization.".format(patient_count))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        add_person_into_person_organization()
