import json
import csv
import math
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
from random import seed
from random import randint
from pytz import timezone
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from common.enums import Status
from core.models import ScriptFileStorage, Person
from core.permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    IsSuperUser,
)

from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus, OrderTrackingStatus, SystemPlatforms
from pharmacy.models import StockIOLog, Purchase, Stock, Product, StockIOLog, OrderTracking

def getEnumString(enums, value):
    data = enums.get_as_tuple_list()
    for item in data:
        if value == item[1]:
            return item[0]

class OrderDetails(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission, )


    def get(self, request, format=None):

        tz = pytz.timezone('Asia/Dhaka')
        date_format = '%Y-%m-%d %H:%M:%S'

        order_id = request.GET.get('order_id', False)
        order = None

        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }
        values_list = [
            'id',
            'organization__id',
            'organization__name',
            'organization__primary_mobile',
            'organization__address',
            'created_at',
            'system_platform',
            'geo_location_data',
            'amount',
            'discount',
            'grand_total',
            'current_order_status',
            'responsible_employee__first_name',
            'responsible_employee__last_name'
        ]

        order_details = Purchase.objects.select_related(
            'distributor',
            'organization__entry_by',
            'distributor_order_group',
            'responsible_employee__designation__department',
        ).filter(
            **filters
        ).filter(
            id=order_id,
        ).select_related(
            'organization'
        ).values(
            *values_list
        )

        if order_details.exists() is False:
            return Response(
                "Not Found",
                status=status.HTTP_200_OK
            )

        order_details=order_details[0]
        organization_id = order_details.pop("organization__id")
        order_id = order_details.pop("id")
        order_details["01 : Order ID"] = order_id
        order_details["02 : Pharmacy"] = order_details.pop("organization__name")
        order_details["03 : Mobile"] = order_details.pop("organization__primary_mobile")
        order_details["04 : Address"] = order_details.pop("organization__address")
        order_details["05 : Order Place Time"] = order_details.pop("created_at").astimezone(tz).strftime("%m/%d/%Y, %I:%M %p")
        order_details["06 : Platfrom"] = getEnumString(SystemPlatforms,order_details.pop("system_platform"))
        order_details["07 : Bill"] = order_details.pop("amount")
        order_details["08 : Discount"] = order_details.pop("discount")
        order_details["09 : Payment"] = order_details.pop("grand_total")
        order_details["10 : Status"] = getEnumString(OrderTrackingStatus, order_details.pop("current_order_status"))
        order_details["11 : Responsible"] = "{} {}".format(
            order_details.pop("responsible_employee__first_name"),
            order_details.pop("responsible_employee__last_name")
        )
        order_details["12 : Location"] = order_details.pop("geo_location_data")

        order_track = pd.DataFrame(OrderTracking.objects.filter(
            order__id=order_id
        ).values(
            'id',
            'date',
            'entry_by__first_name',
            'entry_by__last_name',
            'order_status',
        ).order_by('id'))

        order_track['by'] = order_track['entry_by__first_name'] + " " + order_track['entry_by__last_name']

        order_track['status'] = order_track['order_status'].apply(lambda x: getEnumString(OrderTrackingStatus, x) )

        order_track['time'] = order_track['date'].apply(lambda x: x.astimezone(tz).strftime("%m/%d/%Y, %I:%M %p") )

        order_track['description'] = order_track['status'] + " by " + order_track['by'] + " on " + order_track['time']
        
        order_track=order_track.drop(
            columns=['id', 'date' ,'entry_by__first_name', 'entry_by__last_name', 'order_status' , 'by', 'status', 'time' ]
        ).reset_index(drop=True)

        next_orders_list = pd.DataFrame(Purchase.objects.select_related(
            'distributor',
        ).filter(
            **filters
        ).filter(
            id__gt=order_id,
            organization__id=organization_id,
        ).select_related(
            'organization'
        ).values(
            'id',
            'created_at',
            'grand_total',
            'current_order_status',
            'responsible_employee__first_name',
            'responsible_employee__last_name'

        )[:5])

        if len(next_orders_list.index) > 0:
            next_orders_list['url'] = next_orders_list['id'].apply(lambda x:  "http://app.omisbd.com/api/v1/pharmacy/log/order/?order_id={}".format(x) )
            next_orders_list['time'] = next_orders_list['created_at'].apply(lambda x: x.astimezone(tz).strftime("%m/%d/%Y, %I:%M %p") )
            next_orders_list['price'] = next_orders_list['grand_total'].apply(lambda x:  "{} Taka".format(x) )
            next_orders_list['status'] = next_orders_list['current_order_status'].apply(lambda x: getEnumString(OrderTrackingStatus, x) )
            next_orders_list['by_1'] = next_orders_list['responsible_employee__first_name'].apply(lambda x: str(x) )
            next_orders_list['by_2'] = next_orders_list['responsible_employee__last_name'].apply(lambda x: str(x) )
            next_orders_list['by'] = next_orders_list['by_1'] + " " + next_orders_list['by_2']


        next_orders_list=next_orders_list.drop(
            columns=[
                'id', 'created_at', 'grand_total', 'current_order_status', 'responsible_employee__first_name', 
                'responsible_employee__last_name', 'by_1', 'by_2'
            ]
        ).reset_index(drop=True)

        data = {
            'order' : order_details,
            'changes' : order_track,
            'next' : next_orders_list.to_records()
        }
        return Response(
            data,
            status=status.HTTP_200_OK
        )
