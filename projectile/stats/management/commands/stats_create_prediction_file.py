import logging
import json
import os
import sys
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import datetime, timedelta, time
from pytz import timezone
from django.core.files import File
from common.enums import Status
from core.enums import FilePurposes
from procurement.helpers import send_procure_alert_to_slack
from procurement.models import ProcureItem
from ecommerce.models import ShortReturnLog
from pharmacy.models import Purchase
from django.core.management.base import BaseCommand
from common.slack_client import send_message_to_slack_channel, send_file_to_slack_channel
from common.mattermost_client import send_message_to_mattermost_channel
from procurement.models import ProcureItem
from core.admin import ScriptFileStorage
from django.db.models import Sum, Count
from tabulate import tabulate

localtz = timezone('Asia/Dhaka')
date_format = '%Y-%m-%d %H:%M:%S'


logger = logging.getLogger(__name__)

def store_file(file):
    data_list = []
    with open(file, 'rb') as fi:
        outfile = File(fi, name=os.path.basename(fi.name))
        file_storage = \
            ScriptFileStorage.objects.create(
            content=outfile,
            file_purpose=FilePurposes.SCRIPT,
            entry_by_id=1015
        )
        file_storage.save()

        file_url = "{}/{}".format("https://healthos-media.s3.amazonaws.com",file_storage.content)
        return file_url

def file_generate():

    try:
        FOR_TODAY = True

        days_offset = 0

        if not FOR_TODAY:
            days_offset = 1


        dt_start = datetime.now(
                timezone('Asia/Dhaka')
            ).replace(
                day=datetime.now(
                    timezone('Asia/Dhaka')
                ).day - days_offset,
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

        dt_end = dt_start.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999
        )

        purchase_date = '{}'.format(dt_start.strftime('%Y_%m_%d'))
        time_stamp = '{}'.format(
            datetime.now(
                timezone('Asia/Dhaka')
            ).strftime('%Y_%m_%d_%H_%M_%S')
        )

        data = ProcureItem.objects.filter(
            date__lte=dt_end,
            date__gte=dt_start,
            status=Status.ACTIVE
        ).values(
            'stock__id',
            'procure',
            'procure__supplier__company_name',
            'product_name',
            'company_name',
            'rate',
            'quantity',
            'prediction_item__sale_price',
            'prediction_item__avg_purchase_rate',
            'entry_by__first_name',
            'entry_by__last_name',
            'procure__operation_start',
            'procure__operation_end',
        )

        data = pd.DataFrame(data)

        data['BY'] = data['entry_by__first_name'] + ' ' \
            + data['entry_by__last_name']

        data = data.rename(columns={
            'stock__id': 'ID',
            'procure__supplier__company_name' : 'SUPPLIER',
            'product_name': 'PRODUCT',
            'company_name': 'COM',
            'prediction_item__sale_price': 'SALES',
            'quantity': 'QTY',
            'prediction_item__avg_purchase_rate': 'PRE_PUR',
            'rate': 'PUR',
            'procure__operation_start' : 'OP_START',
            'procure__operation_end' : 'OP_END',
        })

        data['PROFIT'] = data['SALES'] - data['PUR']
        data['DELTA'] = data['PRE_PUR'] - data['PUR']
        data['TOTAL_PROFIT'] = data['PROFIT'] * data['QTY']
        data['PUR_VAL'] = data['PUR'] * data['QTY']
        data['TIME'] = data['OP_END'] - data['OP_START']
        data['SALES_VAL'] = data['QTY']*data['SALES']


        data.drop(['entry_by__first_name', 'entry_by__last_name', 'OP_START' , 'OP_END'],
                  inplace=True, axis=1)


        buyers = data.BY.unique()

        incentive_rate = 0.25

        output = {
            'BUYER': [],
            'UNIQUE_ITEM': [],
            'OP_UNIQUE_ITEM': [],
            'OP_BOX': [],
            'OP_VALUE': [],
            'UP_UNIQUE_ITEM': [],
            'UP_BOX': [],
            'UP_VALUE': [],
            'INCENTIVE': [],
            'TOTAL_PURCHASE': [],
            'SALES_VAL' : [],
            'MARGIN' : []
        }

        for buyer in buyers:

            output['BUYER'].append(buyer)
            buyer_df = data[data.BY == buyer]

            purchase_value = int(buyer_df['PUR_VAL'].sum())

            output['TOTAL_PURCHASE'].append(round(purchase_value,2) )

            unique_item = len(buyer_df.ID.unique())
            output['UNIQUE_ITEM'].append(unique_item)
            op_unique_item = len(buyer_df[(buyer_df.DELTA < 0)
                                 & (buyer_df.PRE_PUR > 0)].ID.unique())
            output['OP_UNIQUE_ITEM'].append(op_unique_item)
            op_box = int(buyer_df[(buyer_df.DELTA < 0) & (buyer_df.PRE_PUR
                         > 0)]['QTY'].sum())
            output['OP_BOX'].append(op_box)

            buyer_op = buyer_df[(buyer_df.DELTA < 0) & (buyer_df.PRE_PUR > 0)]

            buyer_op['VAL'] = buyer_op['QTY'] * buyer_op['DELTA']

            op_val = int(buyer_op['VAL'].sum()) * -1
            output['OP_VALUE'].append(op_val)

            up_unique_item = len(buyer_df[(buyer_df.DELTA > 0)
                                 & (buyer_df.PRE_PUR > 0)].ID.unique())
            output['UP_UNIQUE_ITEM'].append(up_unique_item)

            up_box = int(buyer_df[(buyer_df.DELTA > 0) & (buyer_df.PRE_PUR
                         > 0)]['QTY'].sum())
            output['UP_BOX'].append(up_box)
            incentive = int(up_box * incentive_rate)

            buyer_up = buyer_df[(buyer_df.DELTA > 0) & (buyer_df.PRE_PUR > 0)]
            buyer_up['VAL'] = buyer_up['QTY'] * buyer_up['DELTA']


            up_val = int(buyer_up['VAL'].sum())
            output['UP_VALUE'].append(up_val)
            output['INCENTIVE'].append(incentive)
            output['SALES_VAL'].append( round(buyer_df['SALES_VAL'].sum(),2) )
            output['MARGIN'].append(
                round( 100*((buyer_df['SALES_VAL'].sum()-purchase_value)/buyer_df['SALES_VAL'].sum()), 2)

            )

        output_df = pd.DataFrame(output)

        output_df.to_csv('buyer_output.csv')

        if not data.empty:
            file_name1 = 'PURCHASE_INFO_{}_{}.csv'.format(purchase_date,
                                                          time_stamp)

            data.to_csv(file_name1, encoding='utf-8', index=False)

            file_url = store_file(file_name1)

            send_procure_alert_to_slack("Purchase info has been generated, access it using : {}".format(file_url))


        if not output_df.empty:

            file_name2 = 'BUYER_SUMMARY_{}_{}.csv'.format(purchase_date,
                                                          time_stamp)
            output_df.to_csv(file_name2, encoding='utf-8', index=False)

            file_url = store_file(file_name2)

            send_procure_alert_to_slack("Buyers summary info has been generated, access it using : {}".format(file_url))


        filtered_data = data[data['PRE_PUR'] > 0]

        total_box = filtered_data['QTY'].sum()
        total_purchase_amount = filtered_data['PUR_VAL'].sum()
        total_sales_amount = filtered_data['SALES_VAL'].sum()

        total_profit_amount = filtered_data['TOTAL_PROFIT'].sum()
        profit_margin = (total_profit_amount/total_sales_amount)*100


        slack_msg = "On *`{}`* total *`{}`* box medicine purchased for *`{}M`*, estimated profit is *`{}K`*, estimated margin is *`{}%`*".format(
            dt_start.strftime('%D'),
            str(round(total_box, 0)),
            str(round(total_purchase_amount/1000000 , 2)),
            str(round(total_profit_amount/1000, 2)),
            str(round(profit_margin, 2))
        )
        logger.info(slack_msg)
        send_procure_alert_to_slack(slack_msg)


        now_time = datetime.now(timezone('Asia/Dhaka'))
        today = datetime.now(timezone('Asia/Dhaka')).date()

        day_24_format_start = now_time

        day_24_format_start = day_24_format_start.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        day_24_format_end = day_24_format_start.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999
        )


        data = Purchase.objects.select_related(
            'distributor',
            'organization',
            'distributor_order_group',
        ).filter(
            created_at__gte=day_24_format_start,
            created_at__lt=day_24_format_end,
            status=13,
            distributor_order_type=2,
            purchase_type=4,
        ).exclude(
            order_status__order_status__in=[7, 8, 10]
        ).values(
            'id',
            'organization__id',
            'grand_total'
        )

        data = pd.DataFrame(data)
        delivery_number = len(data)
        unique_delivery = len(data.organization__id.unique())
        sales_value = data.grand_total.sum()/1000

        sales_msg_format = '''From 12PM - 12PM Update {} \n\n\n
        Number of Invoices : {}
        Unique Delivery    : {}
        Sales Values       : {:.2f}K
        Average Invoice    : {:.2f}K'''.format(
            now_time.ctime(),
            delivery_number,
            unique_delivery,
            sales_value,
            sales_value/unique_delivery
        )

        send_procure_alert_to_slack(sales_msg_format)

        pharmacy_chanel_id = os.environ.get('HOS_PHARMA_CHANNEL_ID', "")

        send_message_to_mattermost_channel(
            pharmacy_chanel_id,
            sales_msg_format
        )

        logger.info(sales_msg_format)


        now_time = datetime.now(timezone('Asia/Dhaka'))
        today = datetime.now(timezone('Asia/Dhaka')).date()
        some_days_ago = today-timedelta(14)

        data = Purchase.objects.select_related(
            'distributor',
            'organization',
            'distributor_order_group',
        ).filter(
            tentative_delivery_date__gte=some_days_ago,
            status=13,
            distributor_order_type=2,
            purchase_type=4,
        ).exclude(
            order_status__order_status__in=[7, 8, 10]
        ).values(
            'tentative_delivery_date',
        ).order_by('tentative_delivery_date').annotate(
            invoices=Count('id'),
            deliveries=Count('organization_id', distinct=True),
            sales=Sum('grand_total'),
        )

        data = pd.DataFrame(data)
        data['sales'] = data['sales']
        data['short']=0
        data['return']=0
        data['date'] = None

        for i, row in data.iterrows():
            date = data.at[i,'tentative_delivery_date']

            short_data = ShortReturnLog.objects.filter(
                status=0,
                order__tentative_delivery_date=date,
                type=1
            ).exclude(
                order__status__in=[7,8,9]
            ).values('order__id','short_return_amount')

            short_data = pd.DataFrame(short_data)

            if not short_data.empty:
                data.at[i,'short'] = short_data['short_return_amount'].sum()


            return_data = ShortReturnLog.objects.filter(
                status=0,
                order__tentative_delivery_date=date,
                type=2
            ).exclude(
                order__status__in=[7,8,9]
            ).values('order__id','short_return_amount')

            return_data = pd.DataFrame(return_data)

            if not return_data.empty:
                data.at[i,'return'] = return_data['short_return_amount'].sum()

            data.at[i,'date'] = date.strftime("%b %d")

        data['net_sales'] = data['sales'] - data['short'] - data['return']

        data['net_sales'] = data['net_sales']
        data['sales'] = data['sales']
        data['short'] = data['short']
        data['return'] = data['return']

        data['sales(M)'] = data['sales'].apply(lambda x: "{}M".format( np.round(x/1000000, decimals=2)) )
        data['short(K)'] = data['short'].apply(lambda x: np.round(x/1000, decimals=2))
        data['return(K)'] = data['return'].apply(lambda x: np.round(x/1000, decimals=2))
        data['net_sales(M)'] = data['net_sales'].apply(lambda x: np.round(x/1000000, decimals=2))

        data = data.reindex(
            columns=[
                'date', 'invoices', 'deliveries', 'sales(M)', 'short(K)', 'return(K)', 'net_sales(M)'
            ]
        )


        data = "```" + tabulate(data, headers='keys', tablefmt='psql') + "```"

        send_message_to_mattermost_channel(
            pharmacy_chanel_id,
            data
        )

        logger.info(sales_msg_format)


        logger.info(data)


    except:
        e = sys.exc_info()[0]
        logger.info(e)


class Command(BaseCommand):

    def handle(self, **options):
        file_generate()
