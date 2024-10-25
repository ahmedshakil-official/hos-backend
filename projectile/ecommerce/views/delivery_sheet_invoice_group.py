from ast import Return
import logging
import json
import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from pytz import timezone
from ecommerce.models import DeliverySheetInvoiceGroup
from tqdm import tqdm
from django.core.management.base import BaseCommand
from tabulate import tabulate

from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView

from common.enums import Status
from common.utils import not_blank, prepare_end_date, prepare_start_date
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

from ecommerce.filters import (
    DeliverySheetInvoiceGroupReportFilter,

)


class DeliverySheetInvoiceGroupReport(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    filterset_class = DeliverySheetInvoiceGroupReportFilter

    def get(self, request):
        date = request.query_params.get("date", "")
        _format = "%Y-%m-%d"
        try:
            is_valid_date_format = bool(datetime.strptime(date, _format))
        except ValueError:
            is_valid_date_format = False

        if not is_valid_date_format:
            error = {
                "status": "error",
                "message": f"Wrong date format, please use ({_format}) format as ?date={datetime.today().date()}"
            }
            return Response(
                error,
                status=status.HTTP_400_BAD_REQUEST
            )
        start_date = prepare_start_date(date)
        end_date = prepare_end_date(date)
        order_status = {
            "ACCEPTED": 2,
            "CANCELLED": 8,
            "COMPLETED": 6,
            "DEFAULT": 0,
            "DELIVERED": 5,
            "FULL_RETURNED": 10,
            "OTW": 4,
            "PARTIAL_DELIVERED": 9,
            "PENDING": 1,
            "READY_TO_DELIVER": 3,
            "REJECTED": 7,
            "IN_QUEUE": 11,
            "P_DELIVERED": 12,
            "P_RETURN": 13,
            "P_PARTIAL": 14,
            "P_FAILED": 15,
        }

        ds = DeliverySheetInvoiceGroup.objects.filter(
            delivery_sheet_item__invoice_group_delivery_sheet__status=Status.ACTIVE,
            delivery_sheet_item__invoice_group_delivery_sheet__date__range=[start_date, end_date]
        )

        ds = ds.values(
            "id",
            "invoice_group__order_by_organization__id",
            "invoice_group__order_by_organization__name",
            "invoice_group__responsible_employee__first_name",
            "invoice_group__responsible_employee__last_name",
            "delivery_sheet_item__invoice_group_delivery_sheet__name",
            "delivery_sheet_item__invoice_group_delivery_sheet__coordinator__first_name",
            "delivery_sheet_item__invoice_group_delivery_sheet__coordinator__last_name",
            "delivery_sheet_item__invoice_group_delivery_sheet__created_at",
            "sub_total",
            "grand_total",
            "discount",
            "round_discount",
            "additional_discount",
            "total_short",
            "total_return",
            "invoice_group__current_order_status",
        )

        if not ds.exists():
            return Response({})

        ds = pd.DataFrame(ds)
        ds = ds.rename(
            columns={
                "delivery_sheet_item__invoice_group_delivery_sheet__created_at" : "time",
                "invoice_group__order_by_organization__id": "pharmacy_id",
                "invoice_group__order_by_organization__name": "pharmacy",
                "invoice_group__responsible_employee__first_name": "dm_f",
                "invoice_group__responsible_employee__last_name": "dm_l",
                "delivery_sheet_item__invoice_group_delivery_sheet__name": "work_id",
                "delivery_sheet_item__invoice_group_delivery_sheet__coordinator__first_name": "cod_f",
                "delivery_sheet_item__invoice_group_delivery_sheet__coordinator__last_name": "cod_l",
                "invoice_group__current_order_status": "status",
            }
        )

        ds["delivery_man"] = ds["dm_f"] + " " + ds["dm_l"]
        ds["manager"] = ds["cod_f"] + " " + ds["cod_l"]

        ds.drop(["dm_f", "dm_l", "cod_f", "cod_l"], inplace=True, axis=1)

        data = ds

        for item in order_status:
            data.loc[data["status"] == order_status[item], "status"] = item

        data.reset_index()
        sub_data = pd.pivot_table(
            data,
            values="pharmacy_id",
            index=[ "delivery_man", "work_id"],
            columns=["status"],
            aggfunc=pd.Series.nunique,
            fill_value="0",
        ).reset_index()


        delivery_man_amount = pd.pivot_table(
            data,
            values=["grand_total","total_short"],
            index=["delivery_man",  "work_id"],
            aggfunc=np.sum,
            fill_value="0",
        ).reset_index()



        manager_delviery_man_count = pd.pivot_table(
            data,
            values=["pharmacy_id",],
            index=["manager", "delivery_man" , "work_id"],
            aggfunc=pd.Series.nunique,
            fill_value="0",
        ).reset_index()



        delivery_data =  manager_delviery_man_count.merge(delivery_man_amount, on=['work_id','delivery_man'], how='left')

        delivery_data = delivery_data.rename(
            columns={
                "pharmacy_id": "Assigned Delivery",
                "grand_total" :  "Value",
                "total_short" : "Short",
            }
        )

        time_details = pd.pivot_table(
            data,
            values=["time",],
            index=[ "work_id" ],
            aggfunc=max,
            fill_value="0",
        ).reset_index()

        delivery_data =  delivery_data.merge(time_details, on='work_id', how='left')

        delivery_data['time'] = delivery_data['time'].apply(lambda x: str((x + timedelta(hours=6)).strftime("%b %d %H:%M %p")) ) 

        delivery_data = delivery_data.merge(sub_data, on=['work_id','delivery_man'], how='left')
        delivery_data = delivery_data.to_json(orient='records')
        response_data = json.loads(delivery_data)
        return Response(response_data)