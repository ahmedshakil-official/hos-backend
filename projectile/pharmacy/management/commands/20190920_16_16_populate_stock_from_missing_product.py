import logging
from tqdm import tqdm

from django.db.models import Q, Subquery
from django.core.management.base import BaseCommand

from pharmacy.models import Stock, StorePoint, Product

from common.helpers import (
    get_organization_by_input_id,
)

from common.enums import Status, PublishStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    This management script will take input of an organization and populate
    missing products as stock
    '''

    def handle(self, **options):
        #Get organization name
        organization_instance = get_organization_by_input_id()

        store_points = StorePoint.objects.filter(
            organization=organization_instance,
            status=Status.ACTIVE,
        )
        for store in store_points:
            logger.info("POPULATING MISSING STOCKS OF: **** {} ****".format(store.name))
            discarded_list = Subquery(organization_instance.discarded_products.values('pk'))
            if store.populate_global_product and organization_instance.show_global_product:
                missing_global_products = Product.objects.filter(
                    # (~Q(stock_list__store_point=store) |
                    #  Q(stock_list__status=Status.INACTIVE)),
                    ~Q(stock_list__store_point=store),
                    status=Status.ACTIVE,
                    is_global__in=[
                        PublishStatus.INITIALLY_GLOBAL,
                        PublishStatus.WAS_PRIVATE_NOW_GLOBAL
                    ],
                    # global_category__in=organization_instance.get_global_category()
                ).exclude(pk__in=discarded_list)
                if missing_global_products.count():
                    logger.info("POPULATING {} MISSING GLOBAL PRODUCTS".format(
                        missing_global_products.count()))
                    data_list = []
                    for product in tqdm(missing_global_products):
                        _product_full_name = ' '.join(
                            filter(None, [product.full_name, product.alias_name])
                        )
                        data_list.append(
                            Stock(
                                organization=organization_instance,
                                store_point=store,
                                product=product,
                                is_service=product.is_service,
                                is_salesable=product.is_salesable,
                                product_full_name=_product_full_name.lower(),
                                product_len=len(_product_full_name)
                            )
                        )
                    logger.info("FINISHING POPULATE STOCK....")
                    Stock.objects.bulk_create(data_list)

            missing_local_products = Product.objects.filter(
                # (~Q(stock_list__store_point=store) |
                #  Q(stock_list__status=Status.INACTIVE)),
                ~Q(stock_list__store_point=store),
                organization=organization_instance,
                status=Status.ACTIVE,
                is_global=PublishStatus.PRIVATE,
            ).exclude(pk__in=discarded_list)
            if missing_local_products.count():
                logger.info("POPULATING {} MISSING LOCAL PRODUCTS".format(
                    missing_local_products.count()))
                local_data_list = []
                for product in missing_local_products:
                    _product_full_name = ' '.join(
                        filter(None, [product.full_name, product.alias_name])
                    )
                    local_data_list.append(
                        Stock(
                            organization=organization_instance,
                            store_point=store,
                            product=product,
                            is_service=product.is_service,
                            is_salesable=product.is_salesable,
                            product_full_name=_product_full_name.lower(),
                            product_len=len(_product_full_name)
                        )
                    )
                logger.info("FINISHING POPULATE STOCK....")
                Stock.objects.bulk_create(local_data_list)
