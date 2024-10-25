import json
import os
import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from pharmacy.models import ProductCompartment
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)


def restore_product_compartment():
    logger.info("Importing Product Compartments")
    try:
        # the directory of json file
        data = open(os.path.join(REPO_DIR, 'tmp/product_compartment.json'), 'r')
        json_data = json.load(data)
        compartment_count = 0
        distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        for item in tqdm(json_data):
            try:
                try:
                    ProductCompartment.objects.get(
                        name=item['name'],
                        organization_id=distributor_id
                    )
                except ProductCompartment.DoesNotExist:
                    compartment = ProductCompartment.objects.create(**item, organization_id=distributor_id)

                    compartment_count += 1

            except IntegrityError as exception:
                logger.exception(exception)
                logger.info(item)
                logger.info("{} Product Compartments created".format(compartment_count))
        logger.info("{} Product Compartments created".format(compartment_count))

    except (IntegrityError, IndexError, EOFError, IOError) as exception:
        logger.exception(exception)

    return True


class Command(BaseCommand):
    def handle(self, **options):
        flag = restore_product_compartment()
