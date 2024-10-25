import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from common.enums import Status
from pharmacy.models import Stock

logger = logging.getLogger(__name__)


def get_stock_of_draft_product():

    # return all stocks whose product is draft
    return Stock.objects.filter(
        status=Status.ACTIVE,
        product__status=Status.DRAFT
    ).only(
        'status', 'product'
    )


def change_stock_status(stocks):

    # change the stocks status to draft
    count = 0
    for stock in tqdm(stocks):
        try:
            stock.status = Status.DRAFT
            stock.save(update_fields=['status'])
            count += 1
        except:
            pass
    logger.info("{} Stock is changed to DRAFT - {} Failed".format(count, stocks.count() - count))


class Command(BaseCommand):

    def handle(self, **options):

        logger.info("Changing Stock status to DRAFT")
        # get all stocks whose product is draft
        stocks = get_stock_of_draft_product()
        # change the stocks status to draft
        change_stock_status(stocks)
