import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

from pharmacy.models import (
    ProductCategory,
    ProductForm,
    ProductGeneric,
    ProductGroup,
    ProductManufacturingCompany,
    ProductSubgroup
)

from common.enums import Status

logger = logging.getLogger(__name__)


def change_status(record):
    record.status = Status.DRAFT
    record.save()
    return 1


def change_to_draft_using_reverse_related(model, field_name):
    logger.info("removing unused info of {} model".format(model))
    coutner = 0
    # fetch all record for given model
    data_set = model.objects.filter(status=Status.ACTIVE)
    for data in tqdm(data_set):
        # fetch all check if reverse relation exists
        if hasattr(data, field_name):
            # getting query by reverse relation, and determaining if it has query using exist method
            if not getattr(data, field_name).filter(status=Status.ACTIVE).exists():
                # changing status to draft
                coutner = coutner + change_status(data)

    logger.info("{} record removed from {}".format(coutner, model))

class Command(BaseCommand):

    def handle(self, **options):
        change_to_draft_using_reverse_related(ProductCategory, 'category')
        change_to_draft_using_reverse_related(ProductForm, 'product_form')
        change_to_draft_using_reverse_related(ProductGeneric, 'product_generic')
        change_to_draft_using_reverse_related(ProductSubgroup, 'product_subgroup')
        change_to_draft_using_reverse_related(
            ProductManufacturingCompany,
            'product_manufacturing_company'
        )
        change_to_draft_using_reverse_related(ProductGroup, 'subgroup_product_group')
