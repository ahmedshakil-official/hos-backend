import logging

from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status
from core.models import PersonOrganization, PersonOrganizationSalary
from core.enums import PersonGroupType
logger = logging.getLogger(__name__)


def change_person_organization_type():

    logger.info("CHANGING PERSON ORGANIZATION TYPE..")

    persons = PersonOrganization.objects.all()

    for person in tqdm(persons):
        person.person_group = person.person.person_group
        person.save()

        if person.person_group == PersonGroupType.EMPLOYEE:
            person_organization_salary, created = PersonOrganizationSalary.objects.get_or_create(
                person_organization=person,
                organization=person.organization,
                status=Status.ACTIVE
            )
            if created:
                person_organization_salary.save()

    return True


class Command(BaseCommand):

    def handle(self, **options):
        change_person_organization_type()
