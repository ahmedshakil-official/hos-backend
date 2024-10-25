import logging

from django.core.management.base import BaseCommand

from common.enums import Status
from core.models import OrganizationSetting
from pharmacy.enums import GlobalProductCategory

logger = logging.getLogger(__name__)


def fix_organization_settting():
    logger.info("Fixing Organization Settings who are using private product only")
    organization_settings = OrganizationSetting.objects.filter(
        status=Status.ACTIVE,
        organization__show_global_product=False
    )
    update_count = organization_settings.count()
    organization_settings.update(global_product_category=GlobalProductCategory.DEFAULT)
    logger.info("{} Organization Settings updated.".format(update_count))


class Command(BaseCommand):
    '''
    This management script set global product category
    to DEFAULT who are not using global product
    '''

    def handle(self, **options):
        fix_organization_settting()
