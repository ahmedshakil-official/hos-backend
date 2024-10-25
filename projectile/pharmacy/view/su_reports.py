import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
from django.db.models import (
    Sum,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from common.enums import Status
from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus
from pharmacy.models import StockIOLog, Purchase
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


class DistributorOrganizationOrderSummary(APIView):

    available_permission_classes = (
        IsSuperUser
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, format=None):
        localtz = timezone('Asia/Dhaka')
        date_format = '%Y-%m-%d %H:%M:%S'
        days_to_calculate = int(request.query_params.get('days', 7))
        end_date = datetime.now(timezone('Asia/Dhaka'))
        start_date = end_date - timedelta(days=days_to_calculate)
        io_logs = StockIOLog.objects.filter(
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
                    OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
            ).values_list('id', flat=True),
        ).select_related(
            'stock',
        ).extra(
            select={'day': 'date(date)'}
        ).values(
            'stock__id',
            'stock__product_full_name',
            'day',
            'quantity'
        ).annotate(
            sold=Sum('quantity')
        ).values(
            'stock__id',
            'stock__product_full_name',
            'day',
            'sold'
        ).order_by(
            'stock__id',
            'stock__product_full_name',
            'day',
        )
        sales_data = {
            'id': [],
            'day': [],
            'name': [],
            'sold': [],
        }

        if not io_logs.exists():
            return Response({}, status=status.HTTP_200_OK)

        for data in io_logs:
            sales_data['day'].append(data['day'])
            sales_data['id'].append(data['stock__id'])
            sales_data['name'].append(data['stock__product_full_name'])
            sales_data['sold'].append(data['sold'])
        data_frame = pd.DataFrame.from_dict(sales_data)
        total_order = data_frame.pivot_table(
            index=["id", "name"],
            columns="day",
            values="sold",
            aggfunc="sum",
            margins=True
        ).fillna('-')

        pending_order_io_logs = StockIOLog.objects.filter(
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
                current_order_status=OrderTrackingStatus.ACCEPTED
            ).values_list('id', flat=True),
        ).select_related(
            'stock',
        ).values(
            'stock__id',
            'stock__product_full_name',
            'quantity'
        ).annotate(
            sell_pending=Sum('quantity')
        ).values(
            'stock__id',
            'stock__product_full_name',
            'sell_pending'
        ).order_by(
            'stock__id',
            'stock__product_full_name',
        )
        new_order_data = {
            'id': [],
            'name': [],
            'sell_pending': []
        }
        for data in pending_order_io_logs:
            new_order_data['id'].append(data['stock__id'])
            new_order_data['name'].append(data['stock__product_full_name'])
            new_order_data['sell_pending'].append(data['sell_pending'])
        pending_order = pd.DataFrame.from_dict(new_order_data)
        total_data_frame = total_order.merge(
            pending_order, on=['id', 'name'], how='left')
        total_data_frame['avg'] = total_data_frame['All']/days_to_calculate
        total_data_frame["sell_pending"] = total_data_frame["sell_pending"].fillna(0)
        total_data_frame.drop(['All', 'id'], axis=1, inplace=True)
        # total_data_frame.to_json()
        return Response(
            json.loads(total_data_frame.to_json(date_format='iso', date_unit='s')),
            status=status.HTTP_200_OK
        )
