import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import Q
from core.models import PersonOrganization
from pharmacy.models import StockTransfer
from common.enums import Status

logger = logging.getLogger(__name__)


def get_person_organization(instance, person):
    '''
    Return person organization instance from person
    '''
    if person is not None:
        person_group_type = person.person_group
    else:
        person_group_type = None

    try:
        return PersonOrganization.objects.get(
            organization=instance.organization,
            status=Status.ACTIVE,
            person=person,
            person_group=person_group_type
        )
    except PersonOrganization.DoesNotExist:
        return None


def update_person_organization_in_stock_transfer():
    '''
    Update person organization by and person organization received by
    according to by and received by instance in stock transfer model.
    '''
    try:
        stock_transfer_list = StockTransfer.objects.filter(
            Q(
                by__isnull=False,
                person_organization_by__isnull=True
            ) |
            Q(
                received_by__isnull=False,
                person_organization_received_by__isnull=True
            )
        )
    except IntegrityError, exception:
        logger.exception(exception)
        logger.info(stock_transfer_list)
    update_count = 0
    for stock_transfer in tqdm(stock_transfer_list):
        try:
            stock_transfer.person_organization_by = \
                get_person_organization(
                    stock_transfer,
                    stock_transfer.by
                )
            stock_transfer.person_organization_received_by = \
                get_person_organization(
                    stock_transfer,
                    stock_transfer.received_by
                )
            stock_transfer.save()
            update_count += 1

        except IntegrityError, exception:
            logger.exception(exception)
            logger.info(stock_transfer)
    logger.info("{} Stock Transfer Updated.".format(update_count))


class Command(BaseCommand):
    def handle(self, **options):
        update_person_organization_in_stock_transfer()
