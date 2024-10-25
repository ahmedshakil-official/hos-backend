import logging
from tqdm import tqdm
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from pharmacy.models import Product, Unit
from common.enums import PublishStatus, Status

logger = logging.getLogger(__name__)

unit_name = 'Pcs'

def inactive_unit(products, unit):
    units = Unit.objects.filter(
        name__iexact=unit.name,
        status=Status.ACTIVE,
        organization__isnull=False
    )

    for unit in units:
        unit.status = Status.INACTIVE
        unit.save()

    logger.info(
        "{} unit created, {} product unit is Updated and {} unit is inactivated".format(
            unit.name,
            products.count(),
            units.count()
        )
    )

def replace_unit(products, unit):
    for product in tqdm(products):
        product.primary_unit = unit
        if product.secondary_unit is None:
            product.secondary_unit = unit
        product.conversion_factor = 1
        product.save()

    inactive_unit(products, unit)


def find_unit(unit):
    exist_unit_product = Product.objects.filter(
        Q(primary_unit__name__iexact=unit.name) |
        Q(primary_unit=None),
        status=Status.ACTIVE
    )

    if exist_unit_product:
        replace_unit(exist_unit_product, unit)


def create_global_unit():
    try:
        return Unit.objects.get_or_create(
            status=Status.ACTIVE,
            is_global=PublishStatus.INITIALLY_GLOBAL,
            organization=None,
            name=unit_name
        )
    except IntegrityError as exception:
        logger.exception(exception)


def populate_unit():
    unit = create_global_unit()
    if unit:
        find_unit(unit[0])


class Command(BaseCommand):
    def handle(self, **options):
        populate_unit()
