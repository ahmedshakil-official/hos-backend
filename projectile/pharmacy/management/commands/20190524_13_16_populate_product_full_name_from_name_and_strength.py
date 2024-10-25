import logging

from django.db.models import Q, Value, Case, When
from django.db.models.functions import Concat
from django.core.management.base import BaseCommand

from common.helpers import custom_elastic_rebuild
from pharmacy.models import Product

logger = logging.getLogger(__name__)

def populate_data():

    logger.info("Populating Product")

    products = Product.objects.filter(
        ~Q(full_name=Concat(
            'name',
            Case(
                When(strength__isnull=False, then=Value(' ')),
                default=Value('')
            ),
            'strength'
            )
          )
    )
    update_count = products.count()
    products.update(
        full_name=Concat(
            'name',
            Case(
                When(strength__isnull=False, then=Value(' ')),
                default=Value('')
            ),
            'strength'
        )
    )
    if update_count > 0:
        custom_elastic_rebuild(
            'pharmacy.models.Product', {'strength__isnull': False}
        )
    logger.info("{} Products updated.".format(update_count))


class Command(BaseCommand):
    '''
    This management script to Populate Product's Full Name
    '''
    def handle(self, **options):
        populate_data()
