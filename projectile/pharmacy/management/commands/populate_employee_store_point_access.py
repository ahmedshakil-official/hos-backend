import logging

from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand

from common.enums import Status
from core.models import Person
from core.enums import PersonGroupType
from pharmacy.models import StorePoint, EmployeeStorepointAccess

logger = logging.getLogger(__name__)


def populate_employee_store_point_access():
    logger.info("POPULATING EMPLOYEESTOREPOINTACCESS")
    employees = Person.objects.filter(person_group=PersonGroupType.EMPLOYEE)
    employee_count = 0

    for employee in tqdm(employees):

        store_points = StorePoint.objects.filter(
            Q(organization=employee.organization) &
            (Q(status=Status.ACTIVE) | Q(status=Status.DRAFT)))

        for store in store_points:
            try:
                employee_storepoint_access = EmployeeStorepointAccess.objects.get(
                    employee=employee,
                    store_point=store,
                    organization=employee.organization,
                )
            except EmployeeStorepointAccess.DoesNotExist:
                employee_storepoint_access = EmployeeStorepointAccess.objects.create(
                    organization=employee.organization,
                    employee=employee,
                    store_point=store,
                )
                employee_storepoint_access.save()
                employee_count = employee_count + 1
    logger.info("{} EmployeeStorePointAccess Added".format(employee_count))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        populate_employee_store_point_access()
