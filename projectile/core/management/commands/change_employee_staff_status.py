import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from core.models import Person
from core.enums import PersonGroupType

logger = logging.getLogger(__name__)


def assign_employee_on_organization():
    print "CHANGING EMPLOYEE STAFF STATUS"

    person_list = Person.objects.filter(person_group=PersonGroupType.EMPLOYEE)
    for employee in tqdm(person_list):
        try:
            employee.is_staff = False
            print "Changing status of {}".format(employee)
            employee.save()
        except IntegrityError, e:
            logger.exception(e)
            logger.info(employee)
    return True


class Command(BaseCommand):
    def handle(self, **options):
        assign_employee_on_organization()
