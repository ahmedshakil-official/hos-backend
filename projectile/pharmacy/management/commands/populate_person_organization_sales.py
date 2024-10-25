import logging
from tqdm import tqdm
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import PersonOrganization
from core.enums import PersonGroupType
from pharmacy.models import Sales
from common.enums import Status

logger = logging.getLogger(__name__)


def get_person_organization(sales_instance, person, person_group):
    try:
        return PersonOrganization.objects.get(
            organization=sales_instance.organization,
            status=Status.ACTIVE,
            person=person,
            person_group=person_group
        )

    except PersonOrganization.DoesNotExist:
        return None

def update_person_organization_in_sales():
    try:
        sales_list = Sales.objects.filter(
            Q(buyer__isnull=False, person_organization_buyer__isnull=True) |
            Q(salesman__isnull=False, person_organization_salesman__isnull=True)
        )
    except IntegrityError, exception:
        logger.exception(exception)
        logger.info(sales_list)
    update_count = 0
    for sale in tqdm(sales_list):
        try:
            sale.person_organization_buyer = get_person_organization(
                sale, sale.buyer, PersonGroupType.PATIENT)
            sale.person_organization_salesman = get_person_organization(
                sale, sale.salesman, PersonGroupType.EMPLOYEE)
            if sale.person_organization_salesman is None:
                sale.person_organization_salesman = get_person_organization(
                    sale, sale.salesman, PersonGroupType.SYSTEM_ADMIN)
            sale.save()
            update_count += 1

        except IntegrityError, exception:
            logger.exception(exception)
            logger.info(sale)
    logger.info("{} Sales Object updated.".format(update_count))


class Command(BaseCommand):
    def handle(self, **options):
        update_person_organization_in_sales()
