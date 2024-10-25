import os
import logging

import json
from tqdm import tqdm
from django.db import IntegrityError
from django.core.management.base import BaseCommand

from pharmacy.models import Stock, StockIOLog, StockAdjustment, StorePoint
from core.models import Organization, Person
from pharmacy.enums import StockIOType
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)


def load_data(file_path):

    '''
    This function return date of adjustment as `date`,
    organization that need stock adjustment as `organization`,
    employee who is responsible for this as `employee`
    and `stock_io` note taht stock_io will contain
    `product_id` , `store_point__id`, `batch` & `qty`
    '''

    try:

        # the direcotry of json file

        data = open(os.path.join(REPO_DIR, file_path), 'r')
        result = json.load(data)
        date = result[0]['date']
        organization = Organization.objects.get(pk=result[0]['organization'])
        employee = Person.objects.get(pk=result[0]['organization'])
        stock_io = result[0]['data']

        if stock_io.count == 0:
            # no data for stock adjustment
            stock_io = None

        return date, organization, employee, stock_io

    except Exception, e:

        # error in reading json file
        logger.exception(e)

        return None, None, None, None


def get_stock_status(item, organization_instance):

    '''
    This function will determine what action is needed for given item
    if more products needed to be added then `type` will contain IN
    if products needed to be removed then `type` will contain OUT
    else `type` will contain OTHER
    moreover, id for given stock's will be stored in `data['stock']`,
    and number of product needed to be added / removed will be stored
    on `data['adjustment']`
    '''

    data = {}
    # by default product does not needed to be removed or added
    type_ = 'OTHER'

    try:
        stock = Stock.objects.get(
            store_point=item['store_point'],
            product=item['product'],
            organization=organization_instance
        )

        data['stock'] = stock.id
        data['current_stock'] = stock.stock

        if stock.stock < item['qty']:
            # product should be added in stock
            type_ = 'IN'
            data['adjustment'] = item['qty'] - stock.stock
        elif stock.stock > item['qty']:
            # product should be removed from stock
            type_ = 'OUT'
            data['adjustment'] = stock.stock - item['qty']

    except Stock.DoesNotExist:
        type_ = 'OTHER'

    return type_, data


def append_in_adjustment(type_, item, adjustment_in, adjustment_out):
    '''
    if an item requireed in adjustment, item will be appended
    with `adjustment_in` else with `adjustment_out`

    `adjustment_in`, `adjustment_out` will contain following list
    [
        [
            ALL ITEM IN THIS LIST IS BELONG TO STORE_POINT_A
            {
                'product' : ID,
                'stock_id' : ID_OF_STOCK,
                'batch' : A_BATCH,
                'qty' : CURRENT_STOCK,
                'store_point' : STORE_POINT_A
                'adjustment' : QUANTITY_WILL_GO_ON_STOCK_IO,
                'stock' : STOCK_ID_IN_STOCK_MODAL
            },
            {
                'product' : ID,
                'stock_id' : ID_OF_STOCK,
                'batch' : A_BATCH,
                'qty' : CURRENT_STOCK,
                'store_point' : STORE_POINT_A
                'adjustment' : QUANTITY_WILL_GO_ON_STOCK_IO,
                'stock' : STOCK_ID_IN_STOCK_MODAL
            }

        ],
        [
            ALL ITEM IN THIS LIST IS BELONG TO STORE_POINT_B
            {
                'product' : ID,
                'stock_id' : ID_OF_STOCK,
                'batch' : B_BATCH,
                'qty' : CURRENT_STOCK,
                'store_point' : STORE_POINT_B
                'adjustment' : QUANTITY_WILL_GO_ON_STOCK_IO,
                'stock' : STOCK_ID_IN_STOCK_MODAL
            },
            {
                'product' : ID,
                'stock_id' : ID_OF_STOCK,
                'batch' : B_BATCH,
                'qty' : CURRENT_STOCK,
                'store_point' : STORE_POINT_B
                'adjustment' : QUANTITY_WILL_GO_ON_STOCK_IO,
                'stock' : STOCK_ID_IN_STOCK_MODAL
            }
        ]
    ]
    '''
    key = item['store_point']

    if type_ == 'IN':
        if key in adjustment_in.keys():
            adjustment_in[key].append(item)
        else:
            adjustment_in[key] = [item]

    elif type_ == 'OUT':
        if key in adjustment_out.keys():
            adjustment_out[key].append(item)
        else:
            adjustment_out[key] = [item]

    return adjustment_in, adjustment_out


def stock_adjustment_create(adjustment_date, store_point_instance, employee_instance, organization_instance):

    '''
    Create an stockadjustment instance with given data
    '''
    flag = False
    stock_adjustment = None
    try:
        stock_adjustment = StockAdjustment.objects.create(
            date=adjustment_date,
            store_point=store_point_instance,
            employee=employee_instance,
            organization=organization_instance
        )
        stock_adjustment.save()
        flag = True
    except IntegrityError:
        pass
    return flag, stock_adjustment


def stock_io_create(adjustment_date, item, organization_instance, stock_adjustment, adjustment_type):

    '''
    Create an stock_io instance with given data
    '''

    sub_flag = False

    try:
        stock_io_log = StockIOLog.objects.create(
            date=adjustment_date,
            stock=Stock.objects.get(pk=item['stock_id']),
            type=adjustment_type,
            batch=item['batch'],
            quantity=item['adjustment'],
            organization=organization_instance,
            adjustment=stock_adjustment
        )
        stock_io_log.save()
        sub_flag = True

    except IntegrityError:
        pass

    return sub_flag


def process_stock_io(stock_io, organization):

    adjustment_in = {}
    adjustment_out = {}

    for item in stock_io:

        # travarse through each item to check if this item
        # need any adjustment or not

        type_, data = get_stock_status(item, organization)

        if type_ != 'OTHER':

            # stock need adjustment

            item.update(
                {
                    'adjustment': data['adjustment'],
                    'stock_id': data['stock']
                }
            )

            # adjustment_in will contain all those record what needed to be
            # added with current stock, adjustment_out will contain all those
            # record what needed to be removed from stock

            adjustment_in, adjustment_out = append_in_adjustment(
                type_,
                item,
                adjustment_in,
                adjustment_out
            )

        # wrapping adjustment_in, adjustment_out in adjustments

        adjustments = [
            {'type': StockIOType.INPUT, 'data': adjustment_in},
            {'type': StockIOType.OUT, 'data': adjustment_out}
        ]

    return adjustments

def adjust_stock_on_demand():

    # fetch required data from json file
    date, organization, employee, stock_io = load_data('tmp/stock_adjustment.json')

    if None not in (date, organization, employee, stock_io):

        adjustments = process_stock_io(stock_io, organization)

        for adjustment in tqdm(adjustments):
            for storepoint in adjustment['data'].keys():

                # will travarse through each storepoint which
                # required stock adjustment and create an
                # individual stock adjustment for each storepoint

                store_point_instance = StorePoint.objects.get(pk=storepoint)
                flag, stock_adjustment = stock_adjustment_create(
                    date,
                    store_point_instance,
                    employee,
                    organization
                )
                sub_flag = True

                for item in adjustment['data'][storepoint]:

                    if flag and sub_flag:
                        # will create stock_io for relevent stock adjustment
                        sub_flag = stock_io_create(
                            date,
                            item,
                            organization,
                            stock_adjustment,
                            adjustment['type']
                        )
                    else:
                        # any thing broke while peforming this stock adjustment
                        break

                if flag is False or sub_flag is False:

                    # rollback all entry associated with this stock adjustment

                    StockIOLog.objects.filter(
                        adjustment=stock_adjustment
                    ).delete()
                    stock_adjustment.delete()
    else:
        logger.exception("Failed to make stock adjustment")

    return True


class Command(BaseCommand):
    def handle(self, **options):
        adjust_stock_on_demand()
