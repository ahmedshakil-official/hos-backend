import logging

from itertools import islice
import random
from tqdm import tqdm
from django.db.models import Q, Subquery
from django.core.management.base import BaseCommand
from pharmacy.models import StorePoint, Stock, Product
from common.enums import PublishStatus, Status

from common.helpers import (
    get_organization_by_input_id,
    query_yes_no,
)

logger = logging.getLogger(__name__)

def set_global_product_flag_in_store_point(organization):
    logger.info("UPDATING GLOBAL PRODUCT FLAG FOR ALL STORE POINTS")
    update_count = 0
    store_points = StorePoint.objects.filter(
        status=Status.ACTIVE,
        organization__id=organization.id,
        populate_global_product=False,
    )
    for store_point in tqdm(store_points):
        store_point.populate_global_product = True
        store_point.save(update_fields=['populate_global_product'])
        update_count += 1
    logger.info("GLOBAL PRODUCT FLAG UPDATED FOR {} STORE POINTS".format(update_count))


def fix_global_stock(organization):
    organization_id = organization.id
    logger.info("FIXING GLOBAL STOCK")
    store_points = StorePoint.objects.filter(
        status=Status.ACTIVE,
        organization__id=organization_id,
        populate_global_product=True,
    ).only('id', 'name')
    products = Product.objects.filter(
        (Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
            Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
            Q(organization__id=organization_id)) &
        Q(status=Status.ACTIVE),
        # global_category__in=organization.get_global_category()
    ).only('id', 'is_service', 'is_salesable', 'alias_name', 'name', 'full_name')
    discarded_list = Subquery(organization.discarded_products.values('pk'))
    products = products.exclude(pk__in=discarded_list)

    for store_point in tqdm(store_points):
        stock_count = 0
        data_list = []

        for product in tqdm(products):
            try:
                stock = Stock.objects.only('id').get(
                    store_point__id=store_point.id,
                    product__id=product.id
                )
            except Stock.DoesNotExist:
                full_name = str(product.name)
                if product.name is None:
                    # product name is none then assign empty string
                    full_name = ""

                if product.strength:
                    # if had strength append strength
                    full_name = "{} {}".format(product.name, product.strength)

                if product.full_name != full_name:
                    product.full_name = full_name
                    product.save(update_fields=['full_name'])
                # Concat alias_name with full_name for making the search with alias name too
                lower_full_name_with_alias = ' '.join(
                    filter(None, [full_name, product.alias_name])
                ).lower()
                full_name_len = len(lower_full_name_with_alias)
                data_list.append(Stock(
                    organization_id=organization_id,
                    store_point_id=store_point.id,
                    product_id=product.id,
                    is_service=product.is_service,
                    is_salesable=product.is_salesable,
                    product_full_name=lower_full_name_with_alias,
                    product_len=full_name_len

                ))
                stock_count += 1
            except Stock.MultipleObjectsReturned:
                pass

        batch_size = 5000
        start = 0
        stop = 5000
        while True:
            batch = list(islice(data_list, start, stop))
            if not batch:
                break
            Stock.objects.bulk_create(batch, batch_size)
            start += batch_size
            stop += batch_size

        logger.info("{} Stock created for {}".format(stock_count, store_point))


class Command(BaseCommand):
    def handle(self, **options):
        organization_instance = get_organization_by_input_id()
        populate_global_in_all_stores = query_yes_no(
            "Do you want to set `populate_global_product` flag True for all Store Point of {}".format(organization_instance.name.upper())
        )
        if populate_global_in_all_stores:
            set_global_product_flag_in_store_point(organization_instance)
        fix_global_stock(organization_instance)
