from django.core.management.base import BaseCommand
import logging

from django.db.models import F, Value, CharField, Q, Case, When
from django.db.models.functions import Concat
from tqdm import tqdm

from common.enums import Status
from ecommerce.models import ShortReturnItem

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info("Fixing Short return items name")

        short_return_items = ShortReturnItem.objects.filter(
            status=Status.ACTIVE
        ).annotate(
            product_full_name=Case(
                When(
                    Q(stock__product__form__isnull=False) & Q(stock__product__strength__isnull=False),
                    then=Concat(
                        F("stock__product__form__name"),
                        Value(" "),
                        F("stock__product__name"),
                        Value(" "),
                        F("stock__product__strength"),
                        output_field=CharField(),
                    ),
                ),
                When(
                    Q(stock__product__form__isnull=False) & Q(stock__product__strength__isnull=True),
                    then=Concat(
                        F("stock__product__form__name"),
                        Value(" "),
                        F("stock__product__name"),
                        output_field=CharField(),
                    ),
                ),
                When(
                    Q(stock__product__form__isnull=True) & Q(stock__product__strength__isnull=False),
                    then=Concat(
                        F("stock__product__name"),
                        Value(" "),
                        F("stock__product__strength"),
                        output_field=CharField(),
                    ),
                ),
                default=F("stock__product__name"),
                output_field=CharField(),
            )
        ).filter(
            ~Q(product_name__iexact=F('product_full_name'))
        ).values('id', 'product_name', 'product_full_name')

        obj_to_update = []
        for item in tqdm(short_return_items):
            obj_to_update.append(
                ShortReturnItem(
                    id=item['id'],
                    product_name=item['product_full_name']
                )
            )
        ShortReturnItem.objects.bulk_update(
            obj_to_update,
            ['product_name'],
            batch_size=1000
        )
        logger.info("Done")
