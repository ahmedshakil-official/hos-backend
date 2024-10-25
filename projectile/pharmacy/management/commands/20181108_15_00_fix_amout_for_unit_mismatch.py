import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from pharmacy.models import StockIOLog

logger = logging.getLogger(__name__)


def get_all_log_used_secondary_unit():

    # this method return all stock log record
    # what used secondary unit in sales or purchase

    return StockIOLog.objects.filter(
        secondary_unit_flag=True,
    ).only(
        'sales', 'purchase'
    ).exclude(
        sales__isnull=True,
        purchase__isnull=True,
    )


def get_set_of_sales_and_purchase_from_io_log(logs):
    problametic_sales_purchase = set()
    for item in logs:
        if item.sales is not None:
            problametic_sales_purchase.add(item.sales)
        else:
            problametic_sales_purchase.add(item.purchase)
    return problametic_sales_purchase


def is_inconsistent(data_object):
    # this method check if sales or purchase amount match with stock io's amount
    io_logs = data_object.stock_io_logs.get_queryset().values(
        'quantity', 'rate', 'conversion_factor'
    )
    io_amount = 0
    for item in io_logs:
        io_amount = io_amount + \
            (item['quantity'] / item['conversion_factor'] * item['rate'])
    if io_amount == data_object.amount:
        return False
    return True


def fix_stock_io(data_object):
    io_logs = data_object.stock_io_logs.get_queryset()
    for item in io_logs:
        if item.secondary_unit_flag:
            item.rate = (item.rate) / (item.conversion_factor)
            item.save()


class Command(BaseCommand):

    def handle(self, **options):

        # get all log of sales and purchase what have secondary unit
        logs = get_all_log_used_secondary_unit()

        # initialized empty set of sales and purchase
        sales_purchase_list = get_set_of_sales_and_purchase_from_io_log(
            logs)

        for item in tqdm(sales_purchase_list):
            # check if amount is consistent
            if is_inconsistent(item):
                fix_stock_io(item)
