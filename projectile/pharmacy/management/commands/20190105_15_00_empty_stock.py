import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models.signals import pre_save, post_save

from pharmacy.models import (
    StockIOLog,
    Sales,
    Purchase,
    StockAdjustment,
    StockTransfer,
    Stock,
)
from common.helpers import (
    get_organization_by_input_id,
    get_storepoint_by_id,
)

from pharmacy.signals import (
    pre_save_stock_io_log,
    pre_save_stock_transfer,
    post_save_sale,
    post_save_purchase,
    pre_stock_adjustment,
    pre_save_stock,
)

from pharmacy.enums import StockIOType, AdjustmentType
from core.enums import OrganizationType
from common.enums import Status

logger = logging.getLogger(__name__)


def update_every_object_as_inactive(queryset):
    '''
    making every item of queryset inactive
    '''
    for item in tqdm(queryset):
        item.status = Status.INACTIVE
        item.save()

def inactive_stock_io(stock_io_instance):
    '''
    make given stock io inactive without any prior checking or update
    '''
    pre_save.disconnect(pre_save_stock_io_log, sender=StockIOLog)
    stock_io_instance.status = Status.INACTIVE
    stock_io_instance.save()
    pre_save.connect(pre_save_stock_io_log, sender=StockIOLog)


def delete_sales(stock_ios):
    # finding io associated with sales
    sales_io = stock_ios.filter(
        sales__isnull=False).order_by('sales').distinct()

    for item in tqdm(sales_io):
        post_save.disconnect(post_save_sale, Sales)
        item.sales.status = Status.INACTIVE
        item.sales.save()
        post_save.connect(post_save_sale, Sales)


def delete_purchase(stock_ios):
    # finding io associated with purchase
    purchase_io = stock_ios.filter(
        purchase__isnull=False).order_by('purchase').distinct()
    for item in tqdm(purchase_io):
        post_save.disconnect(post_save_purchase, Purchase)
        item.purchase.status = Status.INACTIVE
        item.purchase.save()
        post_save.connect(post_save_purchase, Purchase)


def delete_transfer(stock_ios):
    # finding io associated with transfer
    transfer_io = stock_ios.filter(
        transfer__isnull=False).order_by('transfer').distinct()
    for item in tqdm(transfer_io):
        pre_save.disconnect(pre_save_stock_transfer, StockTransfer)
        item.transfer.status = Status.INACTIVE
        item.transfer.save()
        pre_save.connect(pre_save_stock_transfer, StockTransfer)


def delete_adjustment(stock_ios):
    # finding io associated with adjustment
    adjustment_io = stock_ios.filter(adjustment__isnull=False).exclude(
        adjustment__adjustment_type=AdjustmentType.AUTO).order_by('adjustment').distinct()
    for item in tqdm(adjustment_io):
        pre_save.disconnect(pre_stock_adjustment, StockAdjustment)
        item.adjustment.status = Status.INACTIVE
        item.adjustment.save()
        pre_save.connect(pre_stock_adjustment, StockAdjustment)


class Command(BaseCommand):

    def handle(self, **options):
        '''
        This managemet script empty stock of a given storeoint
        '''

        # taking input of an organization
        organization_instance = get_organization_by_input_id(OrganizationType.PHARMACY)

        # taking input of a storepoint of given organization
        storepoint_instance = get_storepoint_by_id(
            organization_instance, "Enter Storepoint ID : ")

        # fetching all stock ios
        stock_ios = StockIOLog.objects.filter(
            stock__store_point=storepoint_instance
        )

        # delete all sales
        delete_sales(stock_ios)

        # delete purchase
        delete_purchase(stock_ios)

        # delete transfer
        delete_transfer(stock_ios)

        # delete adjustment except auto
        delete_adjustment(stock_ios)

        # finding all active stock entries of given storepoint
        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            store_point=storepoint_instance,
            stock__gt=0.00
        )

        # making all stock io log in active
        stock_ios = stock_ios.exclude(status=Status.INACTIVE)

        for item in tqdm(stock_ios):
            inactive_stock_io(item)

        # making all stock zero
        for item in tqdm(stocks):
            pre_save.disconnect(pre_save_stock, sender=Stock)
            item.stock = 0.00
            item.save()
            pre_save.connect(pre_save_stock, sender=Stock)