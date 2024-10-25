import logging
from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand
from common.enums import Status
from core.enums import PersonGroupType
from core.models import PersonOrganization
from pharmacy.models import Purchase

logger = logging.getLogger(__name__)


def get_person_ogranization(purchase_instance, person_group_type):
    person_instance = None
    if person_group_type == PersonGroupType.SUPPLIER:
        person_instance = purchase_instance.supplier
    elif person_group_type == PersonGroupType.EMPLOYEE:
        person_instance = purchase_instance.receiver

    try:
        return PersonOrganization.objects.get(
            organization=purchase_instance.organization,
            person=person_instance,
            status=Status.ACTIVE,
            person_group=person_group_type
        )
    except PersonOrganization.DoesNotExist:
        logger.info(
            "Entity for {} {} {} does not exists".format(
                purchase_instance.receiver,
                purchase_instance.supplier,
                purchase_instance.organization
            )
        )
        return None


def populate_purchase_fields():

    logger.info(
        "UPDATING PERSON ORGANIZATION SUPPLIER AND PERSON ORGANIZATION EMPLOYEE")

    purchase_list = Purchase.objects.filter(
        Q(supplier__isnull=False, person_organization_supplier__isnull=True) | Q(
            receiver__isnull=False, person_organization_receiver__isnull=True)
    )

    success_count = 0
    error_count = 0

    for purchase in tqdm(purchase_list):

        try:
            if purchase.receiver and purchase.supplier:
                employee_data = get_person_ogranization(
                    purchase, PersonGroupType.EMPLOYEE)
                if employee_data is None:
                    employee_data = get_person_ogranization(
                        purchase, PersonGroupType.SYSTEM_ADMIN)
                purchase.person_organization_receiver = employee_data

                supplier_data = get_person_ogranization(
                    purchase, PersonGroupType.SUPPLIER)
                purchase.person_organization_supplier = supplier_data

            elif purchase.receiver:
                employee_data = get_person_ogranization(
                    purchase, PersonGroupType.EMPLOYEE)
                if employee_data is None:
                    employee_data = get_person_ogranization(
                        purchase, PersonGroupType.SYSTEM_ADMIN)
                purchase.person_organization_receiver = employee_data
            elif purchase.supplier:
                supplier_data = get_person_ogranization(
                    purchase, PersonGroupType.SUPPLIER)
                purchase.person_organization_supplier = supplier_data

            purchase.save()
            success_count += 1

        except:
            error_count += 1

    logger.info(
        "Successfully updated: {}. Update failed: {}.".format(
            success_count, error_count
        )
    )


class Command(BaseCommand):
    def handle(self, **options):
        populate_purchase_fields()
