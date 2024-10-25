import logging

from tqdm import tqdm
from django.db.models import Q
from django.core.management.base import BaseCommand

from common.enums import Status
from core.enums import PersonGroupType
from core.models import PersonOrganization
from pharmacy.models import StockTransfer

logger = logging.getLogger(__name__)


def get_person_organization(stock_transfer_instance, person_instance):
    # person_instance = None

    try:
        return PersonOrganization.objects.get(
            organization=stock_transfer_instance.organization,
            status=Status.ACTIVE,
            person=person_instance,
            person_group__in=[
                PersonGroupType.EMPLOYEE,
                PersonGroupType.SYSTEM_ADMIN
            ]
        )
    except PersonOrganization.DoesNotExist:
        logger.info(
            "Entity for {} {} {} does not exists".format(
                stock_transfer_instance.by,
                stock_transfer_instance.received_by,
                stock_transfer_instance.organization
            )
        )
        return None


def populate_stock_transfer_fields():

    logger.info("UPDATING STOCK TRANSFER WITH PERSON ORGANIZATION INSTANCE")

    stock_transfer_list = StockTransfer.objects.filter(
        Q(by__isnull=False, person_organization_by__isnull=True) |
        Q(received_by__isnull=False, person_organization_received_by__isnull=True)
    )

    success_count = 0
    error_count = 0

    for stock_transfer in tqdm(stock_transfer_list):

        try:
            if stock_transfer.by and stock_transfer.received_by:
                by_data = get_person_organization(stock_transfer, stock_transfer.by)
                stock_transfer.person_organization_by = by_data

                received_by_data = get_person_organization(
                    stock_transfer, stock_transfer.received_by
                )
                stock_transfer.person_organization_received_by = received_by_data
            elif stock_transfer.by:
                by_data = get_person_organization(stock_transfer, stock_transfer.by)
                stock_transfer.person_organization_by = by_data

            elif stock_transfer.received_by:
                received_by_data = get_person_organization(
                    stock_transfer, stock_transfer.received_by
                )
                stock_transfer.person_organization_received_by = received_by_data

            stock_transfer.save()
            success_count += 1

        except Exception:
            error_count += 1

    logger.info(
        "Updated: {}. Failed: {}.".format(
            success_count, error_count
        )
    )


class Command(BaseCommand):
    def handle(self, **options):
        populate_stock_transfer_fields()
