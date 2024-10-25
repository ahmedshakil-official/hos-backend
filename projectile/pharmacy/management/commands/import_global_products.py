import logging
import random
import string
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import IntegrityError
from pharmacy.models import (
    Product, ProductManufacturingCompany,
    ProductForm, ProductSubgroup, ProductGeneric,
    Unit, ProductCategory,
)
from common.enums import Status, PublishStatus


logger = logging.getLogger(__name__)


def get_random_float(min=0.5, max=500, bigger_then=None):
    if bigger_then is None:
        return random.uniform(min, random.uniform(min + 0.5, max))
    else:
        return random.uniform(bigger_then, random.uniform(bigger_then, bigger_then + 500))


def get_random_object(model_name):
    return model_name.objects.filter(
        Q(status=Status.ACTIVE),
        ~Q(is_global=PublishStatus.PRIVATE)
    ).order_by('?').first()


def create_object(model_name, attribute):
    try:
        obj_instance = model_name.objects.create(**attribute)
        obj_instance.save()
    except IntegrityError as exception:
        logger.error(exception)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('count', help="Number of Products", type=int)

    def handle(self, **options):

        count = options.get('count', 1)

        for ind in tqdm(range(0, count)):
            price_1 = get_random_float()
            price_2 = get_random_float(0.2, 500, price_1)
            product_name = "{} {}Mg".format(''.join(random.choice(string.lowercase) for x in range(
                10
            )), int(get_random_float(0, 500))).capitalize()

            unit = get_random_object(Unit)
            create_object(Product, {
                'name': product_name,
                'purchase_price': price_1,
                'trading_price': price_2,
                'manufacturing_company': get_random_object(ProductManufacturingCompany),
                'form': get_random_object(ProductForm),
                'subgroup': get_random_object(ProductSubgroup),
                'generic': get_random_object(ProductGeneric),
                'is_salesable': True,
                'is_printable': True,
                'is_service': False,
                'primary_unit': unit,
                'secondary_unit': unit,
                'conversion_factor': 1,
                'category': get_random_object(ProductCategory),
                'status': Status.ACTIVE,
                'is_global': PublishStatus.INITIALLY_GLOBAL
            })
