import logging

from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand

from common.enums import Status
from core.enums import PersonGroupType
from core.models import PersonOrganization
from pharmacy.models import StockAdjustment

logger = logging.getLogger(__name__)


def get_person_organization(stock_adjustment_instance, person_group_type):
    person_instance = None
    if person_group_type == PersonGroupType.PATIENT:
        person_instance = stock_adjustment_instance.patient
    elif person_group_type == PersonGroupType.EMPLOYEE or \
            person_group_type == PersonGroupType.SYSTEM_ADMIN:
        person_instance = stock_adjustment_instance.employee

    try:
        return PersonOrganization.objects.get(
            organization=stock_adjustment_instance.organization,
            person=person_instance,
            status=Status.ACTIVE,
            person_group=person_group_type
        )
    except PersonOrganization.DoesNotExist:
        return None
        # raise PersonOrganization.DoesNotExist


def populate_stock_adjustment_fields():

    logger.info("UPDATING STOCK ADJUSTMENT WITH PERSON ORGANIZATION INSTANCE")

    stock_adjustment_list = StockAdjustment.objects.filter(
        Q(employee__isnull=False, person_organization_employee__isnull=True) |
        Q(patient__isnull=False, person_organization_patient__isnull=True)
    )

    success_count = 0
    error_count = 0

    for stock_adjustment in tqdm(stock_adjustment_list):

        try:
            if stock_adjustment.employee:
                stock_adjustment.person_organization_employee = get_person_organization(
                    stock_adjustment,
                    PersonGroupType.EMPLOYEE)
                if stock_adjustment.person_organization_employee is None:
                    stock_adjustment.person_organization_employee = \
                        get_person_organization(
                            stock_adjustment, PersonGroupType.SYSTEM_ADMIN)

            if stock_adjustment.patient:
                stock_adjustment.person_organization_patient = get_person_organization(
                    stock_adjustment,
                    PersonGroupType.PATIENT)

            stock_adjustment.save()
            success_count += 1

        except:
            error_count += 1
            logger.info(
                "Entity for {} {} {} does not exists".format(
                    stock_adjustment.employee,
                    stock_adjustment.patient,
                    stock_adjustment.organization
                )
            )

    logger.info(
        "Updated: {}. Failed: {}.".format(
            success_count, error_count
        )
    )


class Command(BaseCommand):
    def handle(self, **options):
        populate_stock_adjustment_fields()
