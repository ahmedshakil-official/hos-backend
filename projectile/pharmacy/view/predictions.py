import os
import glob
from pathlib import Path
import json
import csv
import math
import pandas as pd
from datetime import datetime, timedelta, time
from dateutil import parser
import pytz
from random import seed
from random import randint
from pytz import timezone
from django.db.models import (
    Sum,
)
from django.core.files import File
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from common.enums import Status
from core.models import ScriptFileStorage, Person
from core.permissions import (
    StaffIsAdmin,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsSalesman,
    CheckAnyPermission,
    IsSuperUser,
)
from core.enums import FilePurposes

from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus, OrderTrackingStatus
from pharmacy.models import StockIOLog, Purchase, Stock, Product, StockIOLog, OrderTracking


def some_time_ago(date):
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start - timedelta(15)
    return end

def find_name(stock_id, data_set):
    return(str(data_set[data_set['stock_id']==stock_id]['product'].iloc[0]))

def find_history(stock_id, dates, data_set):
    data = []
    for date in dates:
        data.append(data_set.loc[(data_set['date'] == date) & (data_set['stock_id'] == stock_id), 'quantity'].sum())
    return str(data)

def find_number(stock_id, dates, data_set):
    data = []
    for date in dates:
        data.append(data_set.loc[(data_set['date'] == date) & (data_set['stock_id'] == stock_id), 'quantity'].sum())
    return sum(data)

def get_startdt_and_enddt_and_date(date):
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(1)
    return start, end, start.date()

def get_date(date, days):
    start = date.replace(hour=6, minute=0, second=0, microsecond=0)
    end = start - timedelta(days)
    return end

def get_data(df, stock_id, key ):
    try:
        return df.loc[(df.stock__id == stock_id)][key].values[0]
    except:
        try:
            return df.loc[(df.ID == stock_id)][key].values[0]
        except:
            return 0

def find_purchase_price(stock_id, date=None):

    query_set = StockIOLog.objects.filter(
        organization__id=303,
        stock__id=stock_id,
        status=0,
        purchase__current_order_status=1,
        purchase__distributor_order_type=1,
        purchase__is_sales_return=False,
        purchase__purchase_order_status=1,
        purchase__purchase_type=3,
        purchase__status=0,
        date=date,
    ).values(
        'rate',
        'quantity',
        'discount_total',
        'tax_total',
        'vat_total',
        'round_discount'
    )
    data = pd.DataFrame.from_records(
        list(query_set)
    )

    if data.empty is False:
        data['purchase_value'] = ((data['rate'] * data['quantity']) - data['discount_total'] - data['tax_total'] - data['vat_total'] + data['round_discount'] )
        value = data['purchase_value'].sum()/data['quantity'].sum()
        return value
    return 0

def get_product_stock(exclude_list=[]):
    return Stock.objects.filter(
        store_point__id=408,
        product__in=Product.objects.filter(
            organization_id=303,
            is_published=True,
            status=0
        ).values_list('id'),

        status=0
    ).exclude(id__in=exclude_list).select_related(
        'product'
    ).values('id','product_full_name', 'product__trading_price', 'product__discount_rate')

def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data)/n # in Python 2 use sum(data)/float(n)

def _ss(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    ss = sum((x-c)**2 for x in data)
    return ss

def stddev(data, ddof=0):
    """Calculates the population standard deviation
    by default; specify ddof=1 to compute the sample
    standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    ss = _ss(data)
    pvar = ss/(n-ddof)
    return pvar**0.5

def get_stock_io(start_date, end_date):
    return StockIOLog.objects.filter(
        purchase__id__in=Purchase.objects.select_related(
            'distributor',
            'organization',
            'distributor_order_group',
            'purchase'
        ).filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED, OrderTrackingStatus.FULL_RETURNED
            ]

        ).values_list('id',flat=True),
    ).select_related(
        'stock',
        'stock__product',
    ).extra(
        select={'day': 'date(date)'}
    ).values(
        'stock__id',
        'stock__product_full_name',
        'stock__product__trading_price',
        'day' ,
        'quantity'
    ).annotate(
        sold=Sum('quantity')
    ).values(
        'stock__id',
        'stock__product_full_name',
        'stock__product__trading_price',
        'day' ,
        'sold'
    ).order_by(
        'stock__id',
        'stock__product_full_name',
        'stock__product_trading_price',
        'day' ,
    )

def get_product_sold_ds(day_low, day_high):
    purchase_data = OrderTracking.objects.filter(
        created_at__gte=day_high,
        status=0,
        order_status=OrderTrackingStatus.ON_THE_WAY
    ).values(
            'order'
    )
    products_sold = list(StockIOLog.objects.filter(
        purchase__in=purchase_data,
    ).exclude(
        purchase__in=Purchase.objects.filter(
            status__in=[
                OrderTrackingStatus.FULL_RETURNED,
                OrderTrackingStatus.CANCELLED,
                OrderTrackingStatus.REJECTED,
            ]
        ),
    ).exclude(
    ).values(
        'stock__id',
        'stock__product_full_name',
    ).annotate(
        sold_qty = Sum('quantity'),
    ).order_by(
        'stock__product_full_name',
    ))
    return pd.DataFrame(products_sold)

def get_product_received_ds(day_low, day_high):
    product_received_queryset = StockIOLog.objects.filter(
        purchase__in=Purchase.objects.filter(
            created_at__gte=day_low,
            created_at__lte=day_high,
            status=Status.DRAFT,
            organization__id=303,
            purchase_type=PurchaseType.REQUISITION,
        )
    ).values(
        'stock__id',
        'stock__product_full_name'
    ).annotate(
        in_qty = Sum('quantity'),
    ).order_by(
        'stock__product_full_name',
    )
    products_received = list(product_received_queryset)
    data_products_received = pd.DataFrame(products_received)
    return data_products_received

class PurchasePrediction(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission, )


    def get(self, request, format=None):

        localtz = timezone('Asia/Dhaka')
        date_format = '%Y-%m-%d %H:%M:%S'

        end_date = some_time_ago(datetime.now(timezone('Asia/Dhaka')))
        today = datetime.now(timezone('Asia/Dhaka')).date()


        io_logs = list(StockIOLog.objects.filter(
            purchase__in=Purchase.objects.select_related(
                'distributor',
                'organization',
                'distributor_order_group',
            ).filter(
                created_at__gte=end_date,
                status=Status.DISTRIBUTOR_ORDER,
                distributor_order_type=DistributorOrderType.ORDER,
                purchase_type=PurchaseType.VENDOR_ORDER,
            ).exclude(
                current_order_status__in=[
                    OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED, OrderTrackingStatus.FULL_RETURNED
                ]
            )
        ).values(
            'stock__id',
            'stock__product_full_name',
            'quantity',
            'purchase__purchase_date'
        ))

        tz = pytz.timezone('Asia/Dhaka')
        for item in io_logs :
            item['purchase__purchase_date'] = item['purchase__purchase_date'].replace(tzinfo=pytz.utc).astimezone(tz).date()
            item['days_gap'] = (today - item['purchase__purchase_date']).days


        data = pd.DataFrame(io_logs)

        data = data.rename(columns={
            'purchase__purchase_date': 'date',
            'stock__id' : 'stock_id',
            'stock__product_full_name' : 'product'
        })

        dates = data['date'].sort_index( ascending=False).unique()[8:-1]

        dates_ld = dates[6:]
        dates_3d = dates[4:]
        dates_7d = dates


        products = list(set(data['stock_id'].unique()))

        response = HttpResponse(content_type='text/csv')
        file_name = "purchase_prediction_{}.csv".format(
            datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        )
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)

        writer = csv.writer(response)
        writer.writerow(['id', 'product name', 'history_7_days', 'last_day', '3d', '7d', 'predicted'])

        for item in products:
            ld = find_number(item, dates_ld, data)
            three_d = find_number(item, dates_3d, data)
            seven_d = find_number(item, dates_7d, data)
            pre = (ld + three_d / 3 + seven_d/7)
            writer.writerow(
                [
                    item,
                    find_name(item, data),
                    find_history(item, dates, data),
                    ld,
                    three_d,
                    seven_d,
                    pre
                ]
            )

        return response

def get_sales_return_ds(tf, users_id ):

    users = Person.objects.filter(
        id__in=users_id
    )

    data = StockIOLog.objects.filter(
        purchase__in=Purchase.objects.filter(
            created_at__gte=tf,
            supplier__id__in=users,
            status=Status.ACTIVE,
            is_sales_return=True,
        )
    ).values(
        'stock__id',
        'stock__product_full_name'
    ).annotate(
        return_amount = Sum('quantity'),
    ).order_by(
        'stock__product_full_name',
    )
    return (pd.DataFrame(data))

class StockWritingFormat(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission, )


    def get(self, request, *args, **kwargs):
        stock_file=request.GET.get('stock_file', '')
        last_stock_obj = ScriptFileStorage.objects.get(name=stock_file)
        base_data =  pd.read_csv(last_stock_obj.content)

        seed(1)

        random_range = int(request.GET.get('random_range', 15))
        days = int(request.GET.get('days', 0))

        time_h = get_date(datetime.now(timezone('Asia/Dhaka')),days)
        time_l = get_date(datetime.now(timezone('Asia/Dhaka')), days + 1)


        product_sold = get_product_sold_ds(None,time_h)
        product_recived = get_product_received_ds(
            time_h , datetime.now(timezone('Asia/Dhaka'))
        )

        product_return_in = get_sales_return_ds(time_h, [87107, 87951, 87952])
        product_return_in = product_return_in.rename(columns={'in_qty':'RETURN_IN'})

        product_ambiguous = get_sales_return_ds(time_h, [87108, 87109, 87232])
        product_ambiguous = product_ambiguous.rename(columns={'in_qty':'RETURN_AMB'})

        base_data['check'] = False
        base_data['new_sales'] = 0
        base_data['rec'] = 0
        base_data['sales_return'] = 0
        base_data['amb'] = 0


        # base data          :  base_data
        # sales data         :  product_sold                 -
        # recived data       :  product_recived              +
        # product return     :  product_return_in            +
        # product ambiguos   :  product_ambiguous            check

        for i, row in base_data.iterrows():
            id = base_data.at[i,'ID']

            s_qty = get_data(product_sold,id,'sold_qty')
            base_data.at[i,'new_sales'] = s_qty

            base_data.at[i,'rec'] = get_data(product_recived,id,'in_qty')

            if get_data(product_return_in,id,'return_amount') > 0:
                base_data.at[i,'sales_return'] = get_data(product_return_in,id,'return_amount')

            if get_data(product_ambiguous,id,'return_amount') > 0:
                base_data.at[i,'amb'] = get_data(product_ambiguous,id,'return_amount')
                base_data.at[i,'check'] = True

            if randint(0, random_range) == 0:
                base_data.at[i,'check'] = True

        response = HttpResponse(content_type='text/csv')
        file_name = "stock_write_{}.csv".format(
            datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        )
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)

        writer = csv.writer(response)
        writer.writerow(['ID', 'NAME', 'PREV_STOCK', 'new_sales', 'rec', 'sales_return', 'amb', 'AUTO', 'check'])

        for i, row in base_data.iterrows():
            writer.writerow(
                [
                    base_data.at[i,'ID'],
                    base_data.at[i,'NAME'],
                    base_data.at[i,'PREV_STOCK'],
                    base_data.at[i,'new_sales'],
                    base_data.at[i,'rec'],
                    base_data.at[i,'sales_return'],
                    base_data.at[i,'amb'],
                    base_data.at[i,'PREV_STOCK'] - base_data.at[i,'new_sales'] +  base_data.at[i,'rec'] + base_data.at[i,'sales_return'] + base_data.at[i,'amb'],
                    base_data.at[i,'check'],
                ]
            )

        return response

class AdvPurchasePrediction(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission, )


    def get(self, request, *args, **kwargs):

        stock_file=request.GET.get('stock_file', '')
        prev_days = int(request.GET.get('past', 7))
        predict_days = int(request.GET.get('future', 3))

        last_day=(datetime.now()-timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        first_day=(datetime.now()-timedelta(days=prev_days)).replace(hour=0, minute=0, second=0, microsecond=0)

        last_stock_obj = ScriptFileStorage.objects.get(name=stock_file)
        last_stock_pd =  pd.read_csv(last_stock_obj.content)
        last_stock_pd= last_stock_pd.rename(columns={'STOCK':'PREV_STOCK'})

        new_purchase = Purchase.objects.filter(
            distributor_id=303,
            purchase_type=PurchaseType.VENDOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            current_order_status__in=[
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.PENDING,
            ],
        )

        old_order = Purchase.objects.filter(
            distributor_id=303,
            purchase_type=PurchaseType.VENDOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            created_at__gte=first_day,
            created_at__lte=last_day,
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.CANCELLED,
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.FULL_RETURNED,
            ],
        )

        new_io_logs = StockIOLog.objects.filter(
            purchase__in=new_purchase,
        ).select_related(
            'organization',
            'purchase',
            'stock',
            'stock__product',
        ).values(
            'stock__id',
            'stock__product_full_name'
        ).annotate(
            purchased_qty = Sum('quantity'),
        ).order_by(
            'stock__product_full_name',
        )


        old_io_logs = StockIOLog.objects.filter(
            purchase__in=old_order,
        ).select_related(
            'organization',
            'purchase',
            'stock',
            'stock__product',
        ).values(
            'stock__id',
            'stock__product_full_name'
        ).annotate(
            purchased_qty = Sum('quantity'),
        ).order_by(
            'stock__product_full_name',
        )

        new_order_pd = pd.DataFrame(new_io_logs)
        old_order_pd = pd.DataFrame(old_io_logs)
        new_order_pd['stock_qty'] = 0

        past_days_label = "last_{}_days".format(prev_days)
        pred_days_label = "pred_{}d".format(predict_days)
        short_label = "d{}_short".format(predict_days)

        new_order_pd = new_order_pd.rename(columns={'purchased_qty':'new_order'})
        old_order_pd = old_order_pd.rename(columns={'purchased_qty': past_days_label })


        old_order_pd[pred_days_label] = (old_order_pd[past_days_label]/prev_days)*predict_days

        old_order_pd['new_order'] = 0
        old_order_pd['stock'] = 0
        old_order_pd['d1_short'] = 0
        old_order_pd[short_label] = 0

        for i, row in new_order_pd.iterrows():
            id = new_order_pd.at[i,'stock__id']
            new_order_pd.at[i,'stock_qty'] = get_data(last_stock_pd,id,'PREV_STOCK')

        for i, row in old_order_pd.iterrows():
            id = old_order_pd.at[i,'stock__id']
            old_order_pd.at[i,'stock'] = get_data(new_order_pd,id,'stock_qty')
            old_order_pd.at[i,'new_order'] = get_data(new_order_pd,id,'new_order')

        old_order_pd['d1_short'] = old_order_pd['stock'] - old_order_pd['new_order']
        old_order_pd[short_label] = old_order_pd['stock'] - old_order_pd[pred_days_label]


        old_order_pd = old_order_pd[old_order_pd[short_label]<0].reset_index(drop=True)
        old_order_pd['d1_short_status'] = False

        response = HttpResponse(content_type='text/csv')
        file_name = "purchase_prediction_{}.csv".format(
            datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        )
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)

        writer = csv.writer(response)
        writer.writerow([
            'stock__id', 'stock__product_full_name', past_days_label,
            pred_days_label, 'new_order' , 'stock' , 'd1_short',
            short_label, 'd1_short_status',
        ])

        for i, row in old_order_pd.iterrows():
            d1_short = old_order_pd.at[i,'d1_short']
            d1_status = False
            if d1_short < 0:
                d1_status = True

            writer.writerow(
                [
                    old_order_pd.at[i, 'stock__id'],
                    old_order_pd.at[i, 'stock__product_full_name'],
                    old_order_pd.at[i, past_days_label],
                    math.floor(old_order_pd.at[i, pred_days_label]),
                    old_order_pd.at[i, 'new_order'],
                    old_order_pd.at[i,'stock'],
                    d1_short,
                    math.ceil(
                        old_order_pd.at[i, short_label]
                    ),
                    d1_status
                ]
            )

        return response

class LossProduct(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission, )


    def get(self, request, format=None):

        days_to_calculate = 7
        margin=.02
        end_date = datetime.now(timezone('Asia/Dhaka'))
        start_date = end_date - timedelta(days=days_to_calculate)
        date_list = []

        for date_gap in range(0, days_to_calculate):
            temp_date = end_date - timedelta(days=date_gap)
            date_list.append(get_startdt_and_enddt_and_date(temp_date))
        date_list_rev = date_list[::-1]
        all_stock = get_product_stock()
        date_today = datetime.now()

        product_data = {
            'id' : [] ,
            'name' : [] ,
            'mrp' : [],
            'discount' : [],
            'sales_price' : [],
            'last_purchase' : [],
            'purchase_dev' : [],
            'purchase' : [],
            'purchase_avg' : [],
            'profit' : [],
            'new_sale_price' : [],
            'new_discount' : [],
        }

        for item in all_stock:

            flag = False
            sales_price = (item['product__trading_price'] - item['product__discount_rate']*(item['product__trading_price']/100))
            last_purchase = "{} days ago".format(days_to_calculate)
            flag = False
            purchase_prices_str = []

            for each_date in date_list_rev:
                lpp = find_purchase_price(item['id'], each_date[2])
                if lpp > 0:
                    if flag is False:
                        flag = True
                        last_purchase = each_date[2].strftime("%d/%m/%Y")
                    purchase_prices_str.append("{:.2f}".format(lpp) )

            purchase_prices = [float(x.strip(' "')) for x in purchase_prices_str]

            diff_price_count = len(purchase_prices)
            if diff_price_count >= 1:
                if diff_price_count == 1:
                    avg_purchase = purchase_prices[0]
                else:
                    avg_purchase = mean(purchase_prices)
                profit_margin = 100*((sales_price-avg_purchase)/avg_purchase)
                profit_status = "Neutral"
                if profit_margin > 0:
                    profit_status = "Profit"
                else:
                    profit_status = "Loss"
                flag = True
                if profit_margin < 2:
                    want_to_sale_in = avg_purchase + (avg_purchase)*margin
                    discount_from_mrp = item['product__trading_price'] - want_to_sale_in
                    product_data['id'].append(item['id'])
                    product_data['name'].append(item['product_full_name'])
                    product_data['mrp'].append(item['product__trading_price'])
                    product_data['discount'].append(item['product__discount_rate'])
                    product_data['sales_price'].append(sales_price )
                    product_data['last_purchase'].append(last_purchase)
                    if diff_price_count > 1:
                        new_stddev=stddev(purchase_prices)
                    else:
                        new_stddev=9999
                    product_data['purchase_dev'].append(new_stddev)
                    product_data['purchase'].append(purchase_prices_str)
                    product_data['purchase_avg'].append( round(avg_purchase,2) )
                    product_data['profit'].append( round(profit_margin,2) )
                    product_data['new_sale_price'].append( round(want_to_sale_in, 2)  )
                    new_discount = round((discount_from_mrp/item['product__trading_price'])*100, 2)
                    product_data['new_discount'].append(new_discount)
            # else:
            #     product_data['id'].append(item['id'])
            #     product_data['name'].append(item['product_full_name'])
            #     product_data['mrp'].append(item['product__trading_price'])
            #     product_data['discount'].append(item['product__discount_rate'])
            #     product_data['sales_price'].append(sales_price )
            #     product_data['last_purchase'].append('-')
            #     new_stddev=9999
            #     product_data['purchase_dev'].append(new_stddev)
            #     product_data['purchase'].append('-')
            #     product_data['purchase_avg'].append('-')
            #     product_data['profit'].append(0)
            #     product_data['new_sale_price'].append('-')
            #     new_discount = '-'
            #     product_data['new_discount'].append(new_discount)
        product_data = pd.DataFrame(product_data).sort_values(by='profit', ascending=True).reset_index()
        file_name = "product_price_{}.csv".format(
            datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        )
        return Response(
            json.loads(product_data.to_json(orient="records", date_format='iso', date_unit='s')),
            status=status.HTTP_200_OK
        )


class DistributorOrderPurchasePrediction(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission, )

    def store_file(self, file, data, prediction_on):
        data_list = []
        with open(file, 'rb') as fi:
            outfile = File(fi, name=os.path.basename(fi.name))
            file_storage = ScriptFileStorage.objects.create(
                content=outfile,
                file_purpose=FilePurposes.PURCHASE_PREDICTION,
                entry_by_id=self.request.user.id,
                data=data,
                prediction_on=prediction_on
            )
            file_storage.save()
            file_list = glob.glob('purchase_prediction*.csv')
            for removeable_file in file_list:
                if Path(removeable_file).is_file():
                    os.remove(removeable_file)


    def post(self, request):

        def get_data(df, stock_id, key ):
            try:
                return df.loc[(df.stock__id == stock_id)][key].values[0]
            except:
                try:
                    return df.loc[(df.ID == stock_id)][key].values[0]
                except:
                    return 0

        stock_file=request.data.get('stock_file', '')
        prev_days = int(request.data.get('past', 7))
        predict_days = int(request.data.get('future', 4))
        order_status = request.GET.get('order_status', [OrderTrackingStatus.PENDING, OrderTrackingStatus.ACCEPTED])
        last_order_date_time = request.data.get('last_order_date_time', 1)
        date_time = parser.parse(last_order_date_time)
        last_day=(date_time - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        first_day=(date_time - timedelta(days=prev_days)).replace(hour=0, minute=0, second=0, microsecond=0)
        last_stock_obj = ScriptFileStorage.objects.get(name=stock_file)
        last_stock_pd =  pd.read_csv(last_stock_obj.content)
        last_stock_pd= last_stock_pd.rename(columns={'STOCK':'PREV_STOCK'})
        new_purchase = Purchase.objects.filter(
            distributor_id=303,
            purchase_type=PurchaseType.VENDOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            current_order_status__in=order_status,
        )
        old_order = Purchase.objects.filter(
            distributor_id=303,
            purchase_type=PurchaseType.VENDOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            created_at__gte=first_day,
            created_at__lte=last_day,
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.CANCELLED,
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.FULL_RETURNED,
            ],
        )
        new_io_logs = StockIOLog.objects.filter(
            purchase__in=new_purchase,
            created_at__lte=date_time
        ).select_related(
            'organization',
            'purchase',
            'stock',
            'stock__product',
        ).values(
            'stock__id',
            'stock__product_full_name'
        ).annotate(
            purchased_qty = Sum('quantity'),
        ).order_by(
            'stock__product_full_name',
        )
        old_io_logs = StockIOLog.objects.filter(
            purchase__in=old_order,
        ).select_related(
            'organization',
            'purchase',
            'stock',
            'stock__product',
        ).values(
            'stock__id',
            'stock__product_full_name'
        ).annotate(
            purchased_qty = Sum('quantity'),
        ).order_by(
            'stock__product_full_name',
        )
        new_order_pd = pd.DataFrame(new_io_logs)
        old_order_pd = pd.DataFrame(old_io_logs)
        new_order_pd['stock_qty'] = 0
        past_days_label = "last_{}_days".format(prev_days)
        pred_days_label = "pred_{}d".format(predict_days)
        short_label = "d{}_short".format(predict_days)
        new_order_pd = new_order_pd.rename(columns={'purchased_qty':'new_order'})
        old_order_pd = old_order_pd.rename(columns={'purchased_qty': past_days_label })
        old_order_pd[pred_days_label] = (old_order_pd[past_days_label] / prev_days) * predict_days
        old_order_pd['new_order'] = 0
        old_order_pd['stock'] = 0
        old_order_pd['d1_short'] = 0
        old_order_pd[short_label] = 0
        for i, row in new_order_pd.iterrows():
            id = new_order_pd.at[i,'stock__id']
            new_order_pd.at[i,'stock_qty'] = get_data(last_stock_pd,id,'PREV_STOCK')
        for i, row in old_order_pd.iterrows():
            id = old_order_pd.at[i,'stock__id']
            old_order_pd.at[i,'stock'] = get_data(new_order_pd,id,'stock_qty')
            old_order_pd.at[i,'new_order'] = get_data(new_order_pd,id,'new_order')
        old_order_pd['d1_short'] = old_order_pd['stock'] - old_order_pd['new_order']
        old_order_pd[short_label] = old_order_pd['stock'] - old_order_pd[pred_days_label]
        old_order_pd = old_order_pd[old_order_pd[short_label]<0].reset_index(drop=True)
        old_order_pd['d1_short_status'] = False
        stock_file_name = last_stock_obj.name.split('.', 1)[0]
        file_name = "purchase_prediction_{}_by_{}.csv".format(
            datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
            stock_file_name
        )
        file = old_order_pd.to_csv(file_name, encoding='utf-8', index=False)
        data = {
            'prev_days': prev_days,
            'predict_days': predict_days,
            'order_status': order_status,
            'date_time': str(date_time)
        }
        # Store generated file in remove original
        if not old_order_pd.empty:
           self.store_file(file_name, data, last_stock_obj)
        return Response(
            json.loads(old_order_pd.to_json(orient="records", date_format='iso', date_unit='s')),
            status=status.HTTP_200_OK
        )
