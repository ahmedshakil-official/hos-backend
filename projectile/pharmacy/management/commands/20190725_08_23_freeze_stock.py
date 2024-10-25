import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from common.helpers import (
    get_first_obj_by_name_and_id,
)

from common.enums import (
    Status,
)

from core.models import Organization
from pharmacy.models import (
    StorePoint,
    StockIOLog,
    Sales,
    Purchase,
    StockAdjustment,
    StockTransfer
)

from pharmacy.helpers import (
    stop_inventory_signal,
    start_inventory_signal,
)

from pharmacy.enums import AdjustmentType

logger = logging.getLogger(__name__)


def prepare_data(passed_kwargs):

    organization_id = passed_kwargs['organization_id']
    organization_name = passed_kwargs['organization_name']

    flag = True
    organization = None

    organization = get_first_obj_by_name_and_id(
        Organization, organization_name, organization_id)

    if organization is None:
        logger.info('organization not found')
        flag = False

    return flag, organization


def freeze_stock(organization):

    # stoping all inventory related signal
    stop_inventory_signal()

    logger.info('freezing all stock io')
    StockIOLog.objects.filter(
        organization=organization,
    ).update(
        status=Status.FREEZE
    )
    logger.info('freezing all stock io finished')

    logger.info('freezing all sales')
    Sales.objects.filter(
        organization=organization,
    ).update(
        status=Status.FREEZE
    )
    logger.info('freezing all sales finished')

    logger.info('freezing all purchsae')
    Purchase.objects.filter(
        organization=organization,
    ).update(
        status=Status.FREEZE
    )
    logger.info('freezing  purchsae finished')

    logger.info('freezing all adjustment')
    StockAdjustment.objects.filter(
        organization=organization,
        adjustment_type=AdjustmentType.MANUAL
    ).update(
        status=Status.FREEZE
    )
    logger.info('freezing all adjustment finished')

    logger.info('freezing all transfer')
    StockTransfer.objects.filter(
        organization=organization
    ).update(
        status=Status.FREEZE
    )
    logger.info('freezing transfer all finished')

    logger.info('reseting all stock start')
    storepoints = StorePoint.objects.filter(organization=organization)
    for storepoint in storepoints:
        storepoint.reset_stock()
    logger.info('reseting all stock end')

    # starting all inventory related signal
    start_inventory_signal()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-id', '--organization_id',
                            type=int, help='give organization id', )
        parser.add_argument('-name', '--organization_name',
                            type=str, help='give organization id', )

    def handle(self, *args, **kwargs):

        flag, organization = prepare_data(kwargs)

        if flag and organization is not None:
            freeze_stock(organization)
