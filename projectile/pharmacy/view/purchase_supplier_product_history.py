import json
from datetime import datetime, timedelta
from pytz import timezone
from tqdm import tqdm
import pandas as pd
import numpy as np
from django.db.models import Sum, Max, Min, Avg, F
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.exceptions import APIException

from common.enums import Status
from common.utils import prepare_end_date, string_to_bool, not_blank
from core.views.common_view import (
    ListAPICustomView
)
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
    StaffIsSalesManager,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from core.models import Organization
from pharmacy.enums import (
    DistributorOrderType,
    PurchaseType,
    OrderTrackingStatus,
    PurchaseOrderStatus,
)
from pharmacy.models import Purchase, StockIOLog, StorePoint, Stock
from pharmacy.helpers import get_average_purchase_price
from pharmacy.filters import DistributorOrderListFilter


class PurchaseSupplierInvoiceProductHistory(APIView):

    available_permission_classes = (
        IsSuperUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        organization_id = 303
        store_point_id = 408

        if settings.DEBUG:
            organization_id = 41
            store_point_id = 94

        params_list = [
            'purchase_days_ago',
            'company_id',
            'only_available_on',
            'how_many_purchase_day',
            'from_mrp',
            'discount_from_mrp',
            'invoice_rate',
            'additional_rate',
            'filter_factor',
        ]
        params_data = {}
        error_data = {}
        for param in params_list:
            value = self.request.query_params.get(param, '')
            if not value:
                error_data[param] = "This param is required"
            else:
                params_data[param] = value

        if error_data:
            raise APIException(error_data)

        PURCHASE_DAYS_AGO = int(params_data.get('purchase_days_ago'))
        COMPANY_ID = int(params_data.get('company_id'))
        ONLY_AVIALABLE_ON = string_to_bool(params_data.get('only_available_on'))
        HOW_MANY_PURCHASE_DAY = int(params_data.get('how_many_purchase_day'))
        FROM_MRP = string_to_bool(params_data.get('from_mrp'))
        DISCOUNT_FROM_MRP = float(params_data.get('discount_from_mrp'))
        INVOICE_RATE = float(params_data.get('invoice_rate'))
        ADDITIONAL_RATE = float(params_data.get('additional_rate'))
        FILTER_FACTOR = int(params_data.get('filter_factor'))

        def get_purchase_price(stock_id, purchase_till ):
            date = datetime.now(
                timezone('Asia/Dhaka')
            )

            query_set = StockIOLog.objects.filter(
                organization__id=organization_id,
                stock__id=stock_id,
                status=Status.ACTIVE,
                purchase__current_order_status=OrderTrackingStatus.PENDING,
                purchase__distributor_order_type=DistributorOrderType.CART,
                purchase__is_sales_return=False,
                purchase__purchase_order_status=PurchaseOrderStatus.DEFAULT,
                purchase__purchase_type=PurchaseType.PURCHASE,
                purchase__status=Status.ACTIVE,
                date__lte=date,
                date__gte=purchase_till,
            ).values(
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
                    return data['cost'].sum()/data['qty'].sum() , data['min_price'].min() , data['max_price'].max()
            except:
                return None, None, None
            return None


        def get_supplier(stock_id, purchase_stock_io, supplier_list):

            sub_data = purchase_stock_io.loc[purchase_stock_io['ID']==stock_id].sort_values(by=['QTY'],ascending=False)[0:3]

            suppliers = [None, None, None]
            index = 0
            for i, row in sub_data.iterrows():
                try:
                    _supp = supplier_list[
                        supplier_list['SUPPLIER_ID']==int(row['SUPPLIER'])
                    ]['SUPPLIER'].to_list()[0]

                    suppliers[index] = "{}, R: {}, Q: {}".format(_supp, round(row[3],2), row[2])

                except:
                    suppliers[index]=None
                index = index + 1

            return suppliers[0] , suppliers[1], suppliers[2]

        health_os = Organization.objects.get(id=organization_id)
        store_point = StorePoint.objects.get(id=store_point_id)


        purchase_till = datetime.now(
            timezone('Asia/Dhaka')
        ) - timedelta(PURCHASE_DAYS_AGO)

        # ----------------------------------------------------------------
        # the following section gives all product list
        # ----------------------------------------------------------------

        common_filter = {
            'product__order_limit_per_day__gte' : 0,
            'product__is_published' : True,
            'product__manufacturing_company__id' : COMPANY_ID
        }

        if ONLY_AVIALABLE_ON is True :
            common_filter = {
                'product__order_limit_per_day__gte' : 0,
                'product__is_published' : True,
                'product__manufacturing_company__id' : COMPANY_ID
            }
        else:
            common_filter = {
                'product__manufacturing_company__id' : COMPANY_ID
            }


        all_product = Stock.objects.filter(
            organization=health_os,
            store_point=store_point
        ).filter(
            **common_filter
        ).select_related(
            'product'
        ).values(
            'id',
            'product__form__name',
            'product__manufacturing_company__id',
            'product__manufacturing_company__name',
            'product_full_name',
            'product__trading_price',
            'product__discount_rate',
            'product__order_limit_per_day',
            'product__is_published'
        ).order_by('product_full_name')

        all_product = pd.DataFrame(all_product)

        all_product= all_product.rename(columns={
            'id':'ID',
            'product__form__name' : 'FORM',
            'product__manufacturing_company__id' : 'COM_ID',
            'product__manufacturing_company__name' : 'COM',
            'stock__product_full_name':'NAME',
            'product__trading_price' : 'MRP',
            'product__discount_rate' : 'DIS_RATE',
            'product_full_name' : 'NAME',
            'product__order_limit_per_day' : 'LIMIT',
            'product__is_published' : 'PUBLISHED'
        })


        all_product['SALES_PRICE'] = 0
        all_product['AVG'] = None
        all_product['RANGE'] = None
        all_product['BID'] = None
        all_product['CHANGE'] = None
        all_product['DEAL'] = False
        all_product['KIND'] = "-"
        all_product['STATUS'] = "On"
        all_product['S1'] = ''
        all_product['S2'] = ''
        all_product['S3'] = ''


        # ----------------------------------------------------------------
        # the above section gives all product list
        # ----------------------------------------------------------------


        all_purchase = Purchase.objects.filter(
            status=Status.ACTIVE,
            purchase_type=PurchaseType.PURCHASE,
            purchase_order_status=PurchaseOrderStatus.DEFAULT,
            organization_id=organization_id,
            is_sales_return=False,
            purchase_date__gte=purchase_till,
        ).values_list('id',flat=True)

        filtered_purchase_stock_io = StockIOLog.objects.filter(
            purchase__id__in=all_purchase,
            stock__product__manufacturing_company__id=COMPANY_ID
        ).select_related(
            'purchase',
            'stock',
            'stock_product'
        ).values(
            'stock__id',
            'purchase__person_organization_supplier__id',
        ).annotate(
            qty=Sum('quantity'),
            AVG=Avg('rate'),
        ).order_by(
            'stock__id',
            'purchase__person_organization_supplier__id',
            '-qty',

        )

        purchase_stock_io = pd.DataFrame(filtered_purchase_stock_io)

        purchase_stock_io= purchase_stock_io.rename(columns={
            'stock__id':'ID',
            'purchase__person_organization_supplier__id' : 'SUPPLIER',
            'qty' : 'QTY'
        })


        supplier_list = Purchase.objects.filter(
            status=Status.ACTIVE,
            purchase_type=PurchaseType.PURCHASE,
            purchase_order_status=PurchaseOrderStatus.DEFAULT,
            organization_id=organization_id,
            is_sales_return=False,
            purchase_date__gte=purchase_till
        ).values(
            'person_organization_supplier__id',
            'person_organization_supplier__company_name',
        ).distinct()


        supplier_list = pd.DataFrame(supplier_list)


        supplier_list = supplier_list.rename(columns={
            'person_organization_supplier__id':'SUPPLIER_ID',
            'person_organization_supplier__company_name' : 'SUPPLIER',
        })


        all_product['SALES_PRICE'] = (all_product['MRP']-(all_product['MRP']/100)*all_product['DIS_RATE'])
        all_product['SALES_PRICE'] = all_product['SALES_PRICE'].apply(lambda x: round(x,2))


        for i, row in tqdm(all_product.iterrows()):
            limit = all_product.at[i,'LIMIT']
            avg_p, min_p, max_p = get_purchase_price(all_product.at[i,'ID'], purchase_till)
            s1, s2, s3 = get_supplier(all_product.at[i,'ID'], purchase_stock_io, supplier_list)
            all_product.at[i,'S1']= s1
            all_product.at[i,'S2']= s2
            all_product.at[i,'S3']= s3
            mrp = all_product.at[i,'MRP']
            if avg_p is not None:
                all_product.at[i,'AVG'] = round(avg_p,2)
                all_product.at[i,'RANGE'] = "{} - {}".format(np.round(min_p,2), np.round(max_p,2))
                profit = (all_product.at[i,'SALES_PRICE'] - all_product.at[i,'AVG'])/all_product.at[i,'AVG']

                if FROM_MRP:
                    all_product.at[i,'BID'] = round(mrp - (mrp/100)*DISCOUNT_FROM_MRP,2)
                else:
                    invoice_value = mrp - (mrp/100)*INVOICE_RATE
                    all_product.at[i,'BID'] = round(invoice_value - (invoice_value/100)*ADDITIONAL_RATE,2)

                n_profit = (all_product.at[i,'SALES_PRICE'] - all_product.at[i,'BID'])/all_product.at[i,'BID']
                all_product.at[i,'CHANGE'] = round((n_profit - profit)*100, 2)

                if all_product.at[i,'CHANGE'] >= FILTER_FACTOR:
                    all_product.at[i,'DEAL'] = True


            pub = all_product.at[i,'PUBLISHED']

            if pub == True and limit > 0:
                all_product.at[i,'STATUS'] = "On"
            else:
                all_product.at[i,'STATUS'] = "Off"

        columns = ['COM_ID', 'COM', 'KIND',  'LIMIT', 'PUBLISHED' ]

        all_product.drop(columns, inplace=True, axis=1)
        all_product['NAME'] = all_product['NAME'].str.replace(r' null', '')

        all_product = all_product.sort_values(by='S1')
        data = all_product.to_json(orient='records')

        response_data = json.loads(data)
        return Response(response_data)


class SupplierPurchaseHistory(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsSalesManager,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        organization_id = 303
        store_point_id = 408

        if settings.DEBUG:
            organization_id = 41
            store_point_id = 94

        health_os = Organization.objects.get(id=organization_id)
        store = StorePoint.objects.get(id=store_point_id)
        product_alias_list = self.request.query_params.get('product', '')
        product_alias_list = list(filter(not_blank(), product_alias_list.split(',')))
        person_organization_supplier_alias = request.query_params.get('person', None)
        if not person_organization_supplier_alias:
            person_organization_supplier_alias = request.query_params.get('supplier', None)
        end_datetime =  request.query_params.get('date_1', '')

        purchase = Purchase.objects.filter(
            organization_id=health_os,
            store_point=store,
            is_sales_return=False,
            distributor_order_type=DistributorOrderType.CART,
            status=Status.ACTIVE,
            purchase_type=PurchaseType.PURCHASE,
            purchase_order_status=PurchaseOrderStatus.DEFAULT,
        )

        if person_organization_supplier_alias is not None:
            purchase = purchase.filter(
                person_organization_supplier__alias=person_organization_supplier_alias
            )

        purchase = DistributorOrderListFilter(request.GET, purchase).qs

        purchase = list(set(purchase.values_list('id', flat=True)))

        product_info = StockIOLog.objects.filter(
            purchase_id__in=purchase
        ).exclude(status=Status.INACTIVE)

        if product_alias_list:
            product_info = product_info.filter(
                stock__product__alias__in=product_alias_list,
            )

        product_info = product_info.values(
            'purchase__organization_wise_serial',
            'purchase__supplier_id',
            'purchase__supplier__company_name',
            'purchase__purchase_date',
            'stock__id',
            'stock__product_full_name',
            'quantity',
            'rate',
        ).order_by('-purchase__purchase_date')

        final_data = pd.DataFrame(product_info)
        if final_data.empty:
            return Response({"message": "No data found"}, status=status.HTTP_200_OK)

        final_data = final_data.rename(columns={
            'purchase__organization_wise_serial':'purchase_id',
            'purchase__supplier_id':'supplier_id',
            'purchase__supplier__company_name':'supplier',
            'purchase__purchase_date':'date',
            'stock__id':'stock_id',
            'stock__product_full_name':'product',
        })
        final_data.date = final_data.date.dt.tz_convert('Asia/Dhaka')
        final_data.date = final_data.date.dt.strftime('%Y-%m-%d')
        final_data['avg'] = final_data.apply(lambda item: get_average_purchase_price(item['stock_id'], prepare_end_date(item['date']), person_organization_supplier_alias), axis=1)

        data = final_data.to_json(orient='records')

        response_data = json.loads(data)
        return Response(response_data)