from pytz import timezone, utc
import os
import json
import glob
from pathlib import Path
from tqdm import tqdm
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time
from django.db.models import Sum, F, Min, Max
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.exceptions import APIException

from common.enums import Status
from common.utils import not_blank, prepare_end_date

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
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from pharmacy.enums import (
    DistributorOrderType,
    PurchaseType,
    OrderTrackingStatus,
    PurchaseOrderStatus,
)
from pharmacy.models import Purchase, Stock, StockIOLog
from pharmacy.filters import DistributorOrderListFilter

class PurchaseSupplierProductReceivedHistory(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):

        product_alias_list = self.request.query_params.get('product', '')
        product_alias_list = list(filter(not_blank(), product_alias_list.split(',')))
        person_organization_supplier_alias = request.query_params.get('person', None)
        if not person_organization_supplier_alias:
            person_organization_supplier_alias = request.query_params.get('supplier', None)
        end_datetime =  request.query_params.get('date_1', '')
        ORGANIZATION_ID = os.environ.get('DISTRIBUTOR_ORG_ID', 303)

        def get_purchase_price(stock_id, end_datetime=None, person_organization_supplier_alias=None):

            query_set = StockIOLog.objects.filter(
                organization__id=ORGANIZATION_ID,
                stock__id=stock_id,
                status=Status.ACTIVE,
                purchase__current_order_status=OrderTrackingStatus.PENDING,
                purchase__distributor_order_type=DistributorOrderType.CART,
                purchase__is_sales_return=False,
                purchase__purchase_order_status=PurchaseOrderStatus.DEFAULT,
                purchase__purchase_type=PurchaseType.PURCHASE,
                purchase__status=Status.ACTIVE,
            )

            if end_datetime:
                query_set = query_set.filter(
                    purchase__purchase_date__lte=end_datetime
                )

            if person_organization_supplier_alias is not None:
                query_set = query_set.filter(
                    purchase__person_organization_supplier__alias=person_organization_supplier_alias
                )


            query_set = query_set.values(
                'date',
            ).annotate(
                qty=Sum('quantity'),
                cost=Sum(
                    F('quantity') *
                    F('rate'),
                ),
                min_price=Min(
                    F('rate'),
                ),
                max_price=Max(
                    F('rate'),
                ),

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
                    return data['cost'].sum()/data['qty'].sum(), data['min_price'].min() , data['max_price'].max()
            except:
                return 0, 0, 0
            return None



        # ----------------------------------------------------------------
        # the following section calculate new product received from supplier
        # after stock was counted
        # ----------------------------------------------------------------

        purchase_data = Purchase.objects.filter(
            status=Status.DRAFT,
            organization__id=ORGANIZATION_ID,
            purchase_type=PurchaseType.REQUISITION,
        )
        purchase_data = DistributorOrderListFilter(request.GET, purchase_data).qs

        if person_organization_supplier_alias is not None:
            purchase_data = purchase_data.filter(
                person_organization_supplier__alias=person_organization_supplier_alias
            )
        purchase_data = purchase_data.values_list('pk', flat=True)

        if not product_alias_list:
            product_received_queryset = StockIOLog.objects.filter(
                purchase__in=purchase_data
            ).values(
                'stock__id',
                'purchase__person_organization_supplier__id',
                'purchase__person_organization_supplier__company_name',
                'stock__product_full_name',
                'purchase__purchase_date',
            ).annotate(
                purchased_qty = Sum('quantity'),
            ).order_by(
                'stock__product_full_name',
            )

        else:
            product_received_queryset = StockIOLog.objects.filter(
                purchase__in=purchase_data,
                stock__product__alias__in=product_alias_list,
            ).values(
                'stock__id',
                'purchase__person_organization_supplier__id',
                'purchase__person_organization_supplier__company_name',
                'stock__product_full_name',
                'purchase__purchase_date',
            ).annotate(
                purchased_qty = Sum('quantity'),
            ).order_by(
                'stock__product_full_name',
            )


        products_received = list(product_received_queryset)
        data_products_received = pd.DataFrame(products_received)

        data_products_received = data_products_received.rename(columns={
            'stock__id' : 'ID',
            'purchase__person_organization_supplier__id' : 'SUPPLIER_ID',
            'purchase__person_organization_supplier__company_name' : 'SUPPLIER',
            'stock__product_full_name' : 'NAME',
            'purchased_qty' : 'NEW_PURCHASE',
            'purchase__purchase_date' : 'DATE'
        })

        if data_products_received.empty:
            return Response([])

        data_products_received.DATE = data_products_received.DATE.dt.tz_convert('Asia/Dhaka')
        data_products_received.DATE = data_products_received.DATE.dt.strftime('%Y-%m-%d')

        data_products_received['SUPPLIER_AVG'] = None
        data_products_received['SUPPLIER_MIN'] = None
        data_products_received['SUPPLIER_MAX'] = None

        data_products_received['PRODUCT_AVG'] = None
        data_products_received['PRODUCT_MIN'] = None
        data_products_received['PRODUCT_MAX'] = None

        for i, row in data_products_received.iterrows():
            stock_id       = data_products_received.at[i,'ID']
            supplier_id = data_products_received.at[i,'SUPPLIER_ID']
            date = data_products_received.at[i,'DATE']

            supplier_avg, supplier_min, supplier_max = get_purchase_price(
                stock_id,
                prepare_end_date(date),
                person_organization_supplier_alias
            )
            product_avg, product_min, product_max = get_purchase_price(stock_id, prepare_end_date(date), None)

            data_products_received.at[i,'SUPPLIER_AVG'] = supplier_avg
            data_products_received.at[i,'SUPPLIER_MIN'] = supplier_min
            data_products_received.at[i,'SUPPLIER_MAX'] = supplier_max

            data_products_received.at[i,'PRODUCT_AVG'] = product_avg
            data_products_received.at[i,'PRODUCT_MIN'] = product_min
            data_products_received.at[i,'PRODUCT_MAX'] = product_max

        data = data_products_received.to_json(orient='records')

        response_data = json.loads(data)
        return Response(response_data)