import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from common.enums import Status
from pharmacy.models import Product

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        logger.info("Populating versatile images for products....")
        products = Product.objects.filter(
            status=Status.ACTIVE,
            image__isnull=False
        )
        for product in tqdm(products):
            if product.image:
                try:
                    product_img_warmer = VersatileImageFieldWarmer(
                        instance_or_queryset=product,
                        rendition_key_set='product_images',
                        image_attr='image',
                        verbose=True
                    )
                    num_created, failed_to_create = product_img_warmer.warm()
                except:
                    pass

        logger.info("Done....")