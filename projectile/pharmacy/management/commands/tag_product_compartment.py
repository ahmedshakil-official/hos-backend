import os
import logging

from tqdm import tqdm
import pandas as pd
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from projectile.settings import REPO_DIR
from common.enums import Status
from pharmacy.models import ProductCompartment, Stock, Product
from pharmacy.enums import UnitType

logger = logging.getLogger(__name__)


def tag_product_compartment(sheet_name, compartment_id, compartment_name):
    data = pd.read_excel(os.path.join(REPO_DIR, 'tmp/product_list_with_compartment.xlsx'),  sheet_name=sheet_name)
    data_df = pd.DataFrame(data)
    data_df = data_df.astype({'ID':'int'})
    id_list = data_df['ID'].tolist()
    stocks = Stock.objects.filter(pk__in=id_list)
    product_pk_list = stocks.values_list('product_id', flat=True)
    Product.objects.filter(pk__in=product_pk_list).update(compartment_id=compartment_id)
    stocks.update(rack=compartment_name)


class Command(BaseCommand):
    def handle(self, **options):
        logger.info("Tagging Product Compartment....")
        distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        product_compartments = ProductCompartment.objects.filter(status=Status.ACTIVE).values('id', 'name')
        tablet_capsule_compartment_id = None
        tablet_capsule_compartment_name = None
        pots_compartment_id = None
        pots_compartment_name = None
        syrup_compartment_id = None
        syrup_compartment_name = None
        surgical_items_compartment_id = None
        surgical_items_compartment_name = None
        strips_compartment_id = None
        strips_compartment_name = None
        for compartment in product_compartments:
            if compartment.get('name', '') == 'Tablet & Capsule':
                tablet_capsule_compartment_id = compartment.get('id', None)
                tablet_capsule_compartment_name = compartment.get('name', None)
            elif compartment.get('name', '') == 'Pots':
                pots_compartment_id = compartment.get('id', None)
                pots_compartment_name = compartment.get('name', None)
            elif compartment.get('name', '') == 'Syrup':
                syrup_compartment_id = compartment.get('id', None)
                syrup_compartment_name = compartment.get('name', None)
            elif compartment.get('name', '') == 'Surgical Items':
                surgical_items_compartment_id = compartment.get('id', None)
                surgical_items_compartment_name = compartment.get('name', None)
            elif compartment.get('name', '') == 'Strips':
                strips_compartment_id = compartment.get('id', None)
                strips_compartment_name = compartment.get('name', None)

        if tablet_capsule_compartment_id:
            logger.info(f"Tagging Product Compartment for {tablet_capsule_compartment_name}")
            tag_product_compartment('Rack Products', tablet_capsule_compartment_id, tablet_capsule_compartment_name)
            logger.info("Done!!!")
        if pots_compartment_id:
            logger.info(f"Tagging Product Compartment for {pots_compartment_name}")
            tag_product_compartment('Pot', pots_compartment_id, pots_compartment_name)
            logger.info("Done!!!")
        if syrup_compartment_id:
            logger.info(f"Tagging Product Compartment for {syrup_compartment_name}")
            tag_product_compartment('Syrup', syrup_compartment_id, syrup_compartment_name)
            logger.info("Done!!!")
        if surgical_items_compartment_id:
            logger.info(f"Tagging Product Compartment for {surgical_items_compartment_name}")
            tag_product_compartment('Surgical', surgical_items_compartment_id, surgical_items_compartment_name)
            logger.info("Done!!!")
        if strips_compartment_id:
            logger.info(f"Tagging Product Compartment for {strips_compartment_name}")
            stocks = Stock.objects.filter(organization_id=distributor_id, product__unit_type=UnitType.STRIP)
            product_pk_list = stocks.values_list('product_id', flat=True)
            Product.objects.filter(pk__in=product_pk_list).update(compartment_id=strips_compartment_id)
            stocks.update(rack=strips_compartment_name)
            logger.info("Done!!!")
        logger.info("All Done!!!")
