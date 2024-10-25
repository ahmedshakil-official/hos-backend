import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from common.enums import Status, PublishStatus

from pharmacy.models import Product

logger = logging.getLogger(__name__)

# Convert id into hexadecimal, add padding using '0' and make uppercase


def generate_hexadecimal_id(_id, padding_length):
    number = hex(_id)
    return number[2:].rjust(padding_length, '0').upper()


class Command(BaseCommand):
    '''
    Generate product code by concating organization id with product id
    '''

    def handle(self, **options):
        # Check active product and unpopulated product code
        products = Product.objects.filter(
            status=Status.ACTIVE,
            code__isnull=True
        )
        organization_id = 0
        product_id = 0
        update_count = 0

        logger.info("POPULATING PRODUCT CODE")

        for product in tqdm(products):
            # Check the product is private or global
            if product.is_global == PublishStatus.PRIVATE:
                # Convert the id of the organization into hexadecimal and add padding
                organization_id = str(
                    generate_hexadecimal_id(product.organization.id, 6))
            else:
                organization_id = '000000'

            # Convert the id of the product into hexadecimal and add padding
            product_id = generate_hexadecimal_id(product.id, 6)

            # Concat the organization id with product id to create product code
            product.code = "{}{}".format(organization_id, product_id)
            # Save the product code
            product.save()
            update_count += 1

        if update_count > 0:
            logger.info("{} PRODUCT CODE UPDATED.".format(update_count))
        else:
            logger.info("NOTHING UPDATED")
