import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from core.models import Person, PersonOrganization
from core.enums import PersonGroupType

logger = logging.getLogger(__name__)


def assign_employee_on_organization():
    print "ASSIGNING EMPLOYEE ON ORGANIZATION"

    person_list = Person.objects.filter(person_group=PersonGroupType.EMPLOYEE)
    for employee in tqdm(person_list):
        if hasattr(employee, 'organization'):

            try:
                person_organization = PersonOrganization.objects.get_or_create(
                    person=employee,
                    organization=employee.organization
                )
                logger.info("{}  created".format(person_organization))
            except IntegrityError, e:
                logger.exception(e)
                logger.info(employee)
    return True


class Command(BaseCommand):
    def handle(self, **options):
        assign_employee_on_organization()
