import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta
from pytz import timezone
from django.db.models import F, Sum

from django.core.files import File

from core.enums import FilePurposes
from common.enums import Status
from ecommerce.models import ShortReturnItem, ShortReturnLog
from ecommerce.enums import ShortReturnLogType

from pharmacy.enums import (
    DistributorOrderType,
    PurchaseType,
    OrderTrackingStatus,
    PurchaseOrderStatus,
)
from pharmacy.models import StockIOLog, Purchase
from ecommerce.enums import ShortReturnLogType


dhaka = timezone('Asia/Dhaka')

def get_purchase_price(date, stock_id):
    query_set = StockIOLog.objects.filter(
        organization__id=303,
        stock__id=stock_id,
        status=Status.ACTIVE,
        # purchase__current_order_status=OrderTrackingStatus.PENDING,
        # purchase__distributor_order_type=1,
        purchase__is_sales_return=False,
        purchase__purchase_order_status=PurchaseOrderStatus.DEFAULT,
        purchase__purchase_type=PurchaseType.PURCHASE,
        purchase__status=Status.ACTIVE,
        date__lte=date,
    ).values(
        'date',
    ).annotate(
        qty=Sum('quantity'),
        cost=Sum(
            F('quantity') *
            F('rate'),
        )
    ).order_by(
        '-date',
        'qty',
        'cost'
    )[0:3]

    data = pd.DataFrame.from_records(
        list(query_set)
    )
    try:
        if data['qty'].sum() > 0:
            return data['cost'].sum() / data['qty'].sum()
    except:
        return None
    return None


def get_profit_by_order(order_id):

    try:
        order = Purchase.objects.get(id=order_id)
        close_status = False
        status_for_zero_profit = [
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED,
            OrderTrackingStatus.FULL_RETURNED
        ]

        if order.current_order_status in status_for_zero_profit:
            order.calculated_profit = 0.00
            order.save(update_fields=['calculated_profit'])
            return

        if order.current_order_status in [OrderTrackingStatus.PARITAL_DELIVERED , OrderTrackingStatus.DELIVERED, OrderTrackingStatus.COMPLETED]:
            close_status = True

        additional_discount = order.additional_discount
        date = order.purchase_date
        stock_ios = StockIOLog.objects.filter(
            purchase=order
        ).values(
            'stock__product__name',
            'stock__id',
            'discount_total',
            'rate',
            'quantity'
        )

        short_return_ios = ShortReturnItem.objects.filter(
            short_return_log__in=ShortReturnLog.objects.filter(
                order__in=[order,],
                status=Status.ACTIVE
            )
        ).select_related(
            'short_return_log__in',
            'short_return_log__order',
            'short_return_log__order',

        ).values(
            'stock__id',
            'type',
            'quantity'
        )

        short_ret_data = pd.DataFrame(short_return_ios)
        short_data = pd.DataFrame([])
        ret_data = pd.DataFrame([])


        if short_return_ios.exists() > 0:
            short_data = short_ret_data[short_ret_data['type'] == ShortReturnLogType.SHORT]
            ret_data = short_ret_data[short_ret_data['type'] == ShortReturnLogType.RETURN]

        data = pd.DataFrame(stock_ios)


        data['return']= 0
        data['short']= 0

        data['subtotal'] = data['rate']*data['quantity']
        data['bill'] = data['subtotal']-data['discount_total']
        total_bill = data['bill'].sum()
        data['net_sell_price'] = data['bill'] - (additional_discount/total_bill)*data['bill']
        data['net_unit_sell_price'] = data['net_sell_price'] /  data['quantity']
        net_sales_price = data['net_sell_price'].sum()

        data['net_unit_purchase_price'] = data['stock__id'].apply(lambda x: get_purchase_price(date, x))
        data['net_unit_profit'] = data['net_unit_sell_price'] -  data['net_unit_purchase_price']
        data['net_profit_bf_short_ret'] = data['net_unit_profit'] *  data['quantity']


        for i, row in data.iterrows():
            _id = data.at[i,'stock__id']
            if not short_data.empty:
                data.at[i,'short'] = short_data[short_data['stock__id'] == _id]['quantity'].sum()
            if not ret_data.empty:
                data.at[i,'return'] = ret_data[ret_data['stock__id'] == _id]['quantity'].sum()

        data['net_profit_bf_short_ret'] = data['net_unit_profit'] *  data['quantity']
        data['short_profit'] = data['net_unit_profit'] * data['short']
        data['return_profit'] = data['net_unit_profit']* data['return']

        data['short_amount'] = data['net_unit_sell_price'] * data['short']
        data['return_amount'] = data['net_unit_sell_price'] * data['return']

        profit = round(data['net_profit_bf_short_ret'].sum(), 2)
        total_short = data['short_amount'].sum()
        total_return = data['return_amount'].sum()

        short_profit = data['short_profit'].sum()
        return_profit = data['return_profit'].sum()

        data= data.rename(columns={
            'stock__product__name' : 'name',
            'quantity' : 'qty',
            'net_sell_price': 'sell',
            'net_unit_purchase_price' : 'purchase',
        })

        columns = [
            'stock__id', 'discount_total', 'subtotal' ,
            'bill', 'net_unit_sell_price', 'net_profit_bf_short_ret',
            'short_profit', 'return_profit', 'short_amount' , 'return_amount'
        ]

        data.drop(columns, inplace=True, axis=1)

        details = {
            'total_bill' : net_sales_price,
            'bill_profit' : profit,
            'total_short' : total_short,
            'total_return' : total_return,
            'short_profit' : short_profit,
            'return_profit' : return_profit,
            'net_profit' : profit - short_profit - return_profit,
            'net_rate' : (profit - short_profit - return_profit) / (net_sales_price - total_return - short_profit),
            'last_calculation' : datetime.now(timezone('Asia/Dhaka')),
            'is_close' : close_status,
            'product_log' : data.to_json(orient='records')
        }

        order.profit_data = details
        order.calculated_profit = profit
        order.save(update_fields=['profit_data', 'calculated_profit'])

    except:
        pass
