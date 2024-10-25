import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.enums import Status, PublishStatus

from pharmacy.models import Product

logger = logging.getLogger(__name__)

def compare_product(product_obj_1, product_obj_2):

    if product_obj_1.id == product_obj_2.id:
        return False
    else:
        name_1 = "".join(product_obj_1.name.lower().split())
        name_2 = "".join(product_obj_2.name.lower().split())

        if name_1 in name_2:
            new_name_with_mg = name_1 + "mg"
            new_name_with_ml = name_1 + "ml"
            if new_name_with_mg == name_2 or new_name_with_ml == name_2:
                return True

        return False

class Command(BaseCommand):

    def handle(self, **options):

        counter = 0

        forms = Product.objects.filter(
            status=Status.ACTIVE
        ).exclude(
            is_global=PublishStatus.PRIVATE
        ).order_by().values('form__name').distinct()

        for form in tqdm(forms):
            # logger.info("Testing {} products".format(form['form__name']))
            filter_companies = Product.objects.filter(
                status=Status.ACTIVE,
                form__name=form['form__name']
            ).exclude(
                is_global=PublishStatus.PRIVATE
            ).order_by().values('manufacturing_company__name').distinct()
            for company in filter_companies:
                products_first = Product.objects.filter(
                    status=Status.ACTIVE,
                    form__name=form['form__name'],
                    manufacturing_company__name=company['manufacturing_company__name'],
                ).exclude(
                    is_global=PublishStatus.PRIVATE
                )

                products_compare = Product.objects.filter(
                    status=Status.ACTIVE,
                    form__name=form['form__name'],
                    manufacturing_company__name=company['manufacturing_company__name'],
                ).exclude(
                    is_global=PublishStatus.PRIVATE
                )

                for product in products_first:
                    for compared_product in products_compare:
                        if compare_product(product, compared_product):
                            logger.info(
                                "{} - {}".format(product, compared_product))
                            # compared_product should be merged with product, not vise versa
                            counter = counter + 1

        logger.info("Number of duplicate products : {}".format(counter))
