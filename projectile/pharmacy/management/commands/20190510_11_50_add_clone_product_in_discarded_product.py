import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status, PublishStatus
from pharmacy.models import Product, OrganizationWiseDiscardedProduct

logger = logging.getLogger()


class Command(BaseCommand):
    '''
    This management script will take input of an organization, accounts an employee and two date
    and move all transaction to another account
    '''

    def handle(self, **options):
        logger.info("Populating Discarded Product")
        products = Product.objects.filter(
            status=Status.ACTIVE,
            clone__isnull=False,
        ).exclude(
            is_global__in=[
                PublishStatus.INITIALLY_GLOBAL,
                PublishStatus.WAS_PRIVATE_NOW_GLOBAL,
            ],
            clone__status=Status.INACTIVE
        )
        update_count = 0
        for product in tqdm(products):
            obj, created = OrganizationWiseDiscardedProduct.objects.get_or_create(
                product=product,
                parent=product.clone,
                organization=product.organization,
            )
            if created:
                update_count += 1
        logger.info("***********************************************************")
        logger.info("{} Discarded Product Created".format(update_count))
        logger.info("***********************************************************")
