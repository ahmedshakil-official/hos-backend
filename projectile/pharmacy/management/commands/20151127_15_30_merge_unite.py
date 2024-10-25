import logging
from tqdm import tqdm

from django.db.models import Q
from django.core.management.base import BaseCommand

from common.enums import Status, PublishStatus

from pharmacy.models import (
    Unit,
    Product,
    StockIOLog
)

logger = logging.getLogger()

def take_unit_input():
    unit_id = input("Choose a correct unit id(0 to exit): ")
    return unit_id

def process_unit_input(queryset):
    logger.info("***********************************************************")
    logger.info("ID        Unit")
    for item in queryset:
        unit_id = str(item.id).ljust(10)
        unit_name = item.name.ljust(15)
        logger.info("{}{}".format(unit_id, unit_name))

    logger.info("***********************************************************")

    unit_id = take_unit_input()
    unit = None

    while True:
        try:
            if unit_id == 0:
                return
            unit = Unit.objects.get(id=unit_id)
            if unit:
                break
            else:
                continue
        except Unit.DoesNotExist:
            unit_id = take_unit_input()
    return unit

def take_related_second_unit_input(unit):
    sec_unit = None
    # if given unit is private
    if unit.is_global == PublishStatus.PRIVATE:
        # find other private unit of same organization
        units = Unit.objects.filter(
            status=Status.ACTIVE,
            organization=unit.organization,
            is_global=PublishStatus.PRIVATE,
        )
        if units.exists() and len(units) > 1:
            logger.info("SELECT THE UNIT YOU WANT TO MERGE WITH")
            sec_unit = process_unit_input(units)

    # if given unit is global
    else:
        # find other global unit
        units = Unit.objects.filter(
            Q(status=Status.ACTIVE),
            ~Q(is_global=PublishStatus.PRIVATE)
        )
        if units.exists() and len(units) > 1:
            logger.info("SELECT THE UNIT YOU WANT TO MERGE WITH")
            sec_unit = process_unit_input(units)
    return sec_unit

def check_both_unit_are_valid(unit, sec_unit):
    if (unit is not None and sec_unit is not None) and (unit != sec_unit):
        return True
    return False

def changing_attribute_over_queryset(model, arguments, attribute_name, value):
    arguments.update({'status': Status.ACTIVE})
    queryset_item = model.objects.filter(
        **arguments
    )
    for item in tqdm(queryset_item):
        if hasattr(item, attribute_name):
            setattr(item, attribute_name, value)
            item.save()

def replace_product_with_primary_unit(unit, sec_unit):
    # replace all product with given unit as primary unit with `sec_unit`
    logger.info(
        "REPLACING ALL PRODUCT WHAT CONTAIN `{}` as PRIMARY UNIT".format(unit.name))
    changing_attribute_over_queryset(
        Product,
        {'primary_unit': unit},
        'primary_unit', sec_unit
    )

def replace_product_with_secondery_unit(unit, sec_unit):
    # replace all product with given unit  as secondery unit with `sec_unit`
    logger.info(
        "REPLACING ALL PRODUCT WHAT CONTAIN `{}` as SECONDARY UNIT".format(unit.name))
    changing_attribute_over_queryset(
        Product,
        {'secondary_unit': unit},
        'secondary_unit', sec_unit
    )

def replace_stock_io_with_primary_unit(unit, sec_unit):
    # replace all stock io with given unit as primary unit with `sec_unit`
    logger.info(
        "REPLACING ALL STOCK IO LOG WHAT CONTAIN `{}` as PRIMARY UNIT".format(unit.name))
    changing_attribute_over_queryset(
        StockIOLog,
        {'primary_unit': unit},
        'primary_unit', sec_unit
    )

def replace_stock_io_with_secondery_unit(unit, sec_unit):

    # replace all stock io with given unit  as secondery unit with `sec_unit`
    logger.info(
        "REPLACING ALL STOCK IO LOG WHAT CONTAIN `{}` as SECONDARY UNIT".format(unit.name))
    changing_attribute_over_queryset(
        StockIOLog,
        {'secondary_unit': unit},
        'secondary_unit', sec_unit
    )


class Command(BaseCommand):

    def handle(self, **options):
        units = Unit.objects.filter(status=Status.ACTIVE)

        logger.info("SELECT THE UNIT YOU WANT TO MERGE")

        # Taking any unit
        unit = process_unit_input(units)
        if unit is None:
            return

        # Taking another unt input accordance with fist unit
        sec_unit = take_related_second_unit_input(unit)

        if check_both_unit_are_valid(unit, sec_unit):
            replace_product_with_primary_unit(unit, sec_unit)
            replace_product_with_secondery_unit(unit, sec_unit)
            replace_stock_io_with_primary_unit(unit, sec_unit)
            replace_stock_io_with_secondery_unit(unit, sec_unit)
        else:
            logger.error("UNITS WERE NOT SELECTED PROPERLY")
            return

        unit.status = Status.INACTIVE
        unit.save()
