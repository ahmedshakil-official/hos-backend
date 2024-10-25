import logging

from django.db.models import Q
from django.core.management.base import BaseCommand

from common.enums import Status, PublishStatus
from common.helpers import custom_elastic_rebuild
from core.models import OrganizationSetting
from pharmacy.enums import GlobalProductCategory
from pharmacy.models import Product

logger = logging.getLogger(__name__)


def populate_organization_settting():
    logger.info("Populating Organization Settings")
    organization_settings = OrganizationSetting.objects.filter(
        status=Status.ACTIVE,
        global_product_category=GlobalProductCategory.DEFAULT
    )
    update_count = organization_settings.count()
    organization_settings.update(global_product_category=GlobalProductCategory.GPA)
    logger.info("{} Organization Settings updated.".format(update_count))
    logger.info("<======================================================>")

def populate_data():

    logger.info("Populating Global Product")

    products = Product.objects.filter(
        Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
        Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL),
        status=Status.ACTIVE,
        global_category=GlobalProductCategory.DEFAULT
    )
    update_count = products.count()
    products.update(global_category=GlobalProductCategory.GPA)
    if update_count > 0:
        custom_elastic_rebuild(
            'pharmacy.models.Product',
            {'global_category': GlobalProductCategory.GPA}
        )
    logger.info("{} Products updated.".format(update_count))


class Command(BaseCommand):
    '''
    This management script set global_category
    of all global product to GPA
    '''

    def handle(self, **options):
        populate_organization_settting()
        populate_data()
