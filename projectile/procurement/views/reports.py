
import csv

import numpy as np
import pandas as pd

from django.db.models import Sum, F, Value, CharField
from django.db.models.functions import Concat
from django.http import HttpResponse
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from common.enums import Status, ActionType
from common.utils import prepare_start_date, prepare_end_date
from common.pagination import CachedCountPageNumberPagination

from core.views.common_view import(
    ListCreateAPICustomView,
    CreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)
from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsProcurementOfficer,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
    StaffIsDistributionT1,
)
from ..utils import get_procures_items_with_buyers_from_date_range, create_purchase_csv_response
from procurement.serializers.procure_item import ProcureItemModelSerializer
from ..models import Procure, PurchasePrediction
from ..filters import ProcurementReportProductWiseFilter


class ProcurementReportProductWise(ListAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = ProcurementReportProductWiseFilter
    serializer_class = ProcureItemModelSerializer.ProductWiseReport
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self, related_fields=None, only_fields=None):
        return super().get_queryset(related_fields=related_fields, only_fields=only_fields).select_related(
            'procure',
            'procure__supplier',
            'procure__employee',
            'prediction_item',
        )


class PredictionNotProcuredItemsReport(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)

    lookup_fields = ["alias"]

    def get(self, request, *args, **kwargs):
        import pandas as pd
        from procurement.models import ProcureItem, PredictionItem, PredictionItemMark
        from common.enums import Status

        alias = kwargs.get('alias', '')
        try:

            pred_file = PurchasePrediction.objects.get(
                prediction_file__alias=alias
            )
        except (PurchasePrediction.DoesNotExist, PurchasePrediction.MultipleObjectsReturned):
            return Response(
                {
                    "error": "Object not found"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        prediction_file_id = pred_file.prediction_file_id
        date = pred_file.date

        dt_start = date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        dt_end = date.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999
        )

        data = PredictionItem.objects.filter(
            purchase_prediction=pred_file,
            suggested_purchase_quantity__gt=0
        ).values(
            "id",
            'stock__id',
            'product_name',
            'company_name',
            'mrp',
            'avg_purchase_rate',
            'real_avg',
            'worst_rate',
            'suggested_purchase_quantity',
            'prediction_item_suggestions__supplier__company_name',
            'prediction_item_suggestions__priority',
        )
        # Use a set to avoid duplicate (id, stock__id) tuples
        prediction_item_id_list = set(data.values_list("id", "stock__id"))

        # Create an empty list to store prediction item marks data
        prediction_item_marks_data = []

        for prediction_item_id, stock_id in prediction_item_id_list:
            prediction_item_marks = PredictionItemMark.objects.filter(
                prediction_item_id=prediction_item_id
            ).values(
                'prediction_item__stock__id',
                'rate',
                'remarks'
            )

            for mark in prediction_item_marks:
                prediction_item_marks_data.append({
                    'stock__id': mark['prediction_item__stock__id'],
                    'rating': mark['rate'],
                    'remark': mark['remarks']
                })

        # Convert the list of dictionaries to a DataFrame
        prediction_item_marks_df = pd.DataFrame(
            prediction_item_marks_data, columns=["stock__id", "rating", "remark"]
        )
        prediction_data = pd.DataFrame(data)

        data_prediction = prediction_data.rename(columns={
            'stock__id': 'ID',
            'product_name': 'name',
            'company_name': 'com',
            'avg_purchase_rate': 'mn_rate',
            'worst_rate': 'mx_rate',
            'suggested_purchase_quantity': 'qty',
            'prediction_item_suggestions__supplier__company_name': 'supplier',
            'prediction_item_suggestions__priority': 'sup_prio',
        })
        data = ProcureItem.objects.filter(
            date__lte=dt_end,
            date__gte=dt_start,
            status=Status.ACTIVE
        ).values(
            'stock__id',
        ).order_by('stock__id').annotate(
            procured=Sum('quantity')
        )

        procured_data = pd.DataFrame(data)

        procured_data = procured_data.rename(columns={
            'stock__id': 'ID',

        })

        if prediction_data.empty or procured_data.empty:
            return Response(
                {
                    "error": "No Data Found"
                }
            )

        output = data_prediction.merge(procured_data, on='ID', how='left').fillna(0)
        output['order_qty'] = output['qty'] - output['procured']
        output = output.astype({"qty": "int", "procured": "int", "order_qty": "int", "sup_prio": "int"})
        output = output.astype({"sup_prio": "str"})

        output = output[output['order_qty'] >= 1].reset_index()
        output['value'] = output['order_qty'] * output['real_avg']

        output['mrp'] = output['mrp'].apply(lambda x: round(x, 2))
        output['mn_rate'] = output['mn_rate'].apply(lambda x: round(x, 2))
        output['mx_rate'] = output['mx_rate'].apply(lambda x: round(x, 2))
        output['value'] = output['value'].apply(lambda x: round(x, 2))
        output['shop'] = output['sup_prio'].astype(str) + ") " + output['supplier'].astype(str)
        output = output.drop(['qty', 'procured', 'real_avg', 'supplier', 'sup_prio'], axis=1)

        output = output.groupby(
            ['ID', 'name', 'com', 'mrp', 'mn_rate', 'mx_rate', 'order_qty', 'value'],
            as_index=False).agg(lambda x: ', '.join(set(x.dropna()))
        )

        for _, row in output.iterrows():
            stock_id = row['ID']
            matching_marks = prediction_item_marks_df[prediction_item_marks_df['stock__id'] == stock_id]

            for count, mark in matching_marks.iterrows():
                output.at[_, 'Mark_Rate_{}'.format(count+1)] = mark['rating']
                output.at[_, 'Mark_Remark_{}'.format(count+1)] = mark['remark']

        # generating a columns names list to create a df by it
        csv_column_names = ['ID', 'name', 'com', 'mrp', 'mn_rate', 'mx_rate', 'order_qty', 'value', 'shop']
        original_column_names = csv_column_names.copy()

        # Find the maximum number of rate and remark columns for formatting
        max_rate_columns = output.filter(like='Mark_Rate_').shape[1]
        max_remark_columns = output.filter(like='Mark_Remark_').shape[1]

        # Add rate and remark columns to the CSV column names
        for i in range(1, max_rate_columns + 1):
            csv_column_names.append('Mark_Rate_{}'.format(i))

        for i in range(1, max_remark_columns + 1):
            csv_column_names.append('Mark_Remark_{}'.format(i))

        # Replace empty values with NaN and drop columns where all values are NaN
        output.replace('', np.nan, inplace=True)
        output = output.dropna(axis=1, how='all')

        # Fill NaN values with empty strings for better display
        output.fillna("", inplace=True)
        csv_column_names = output.columns.tolist()

        # extract the rate and remark columns
        rate_remark_columns = [
            column for column in output.columns
            if column.startswith('Mark_Rate_') or column.startswith('Mark_Remark_')
        ]

        # sort the rate and remark columns by the postfix value
        rate_remark_columns.sort(key=lambda x: int(x.split('_')[-1]))


        # extend the original columns with the sorted columns and replace the csv_column_names
        original_column_names.extend(rate_remark_columns)

        # reindex with the updated `original_column_names` name
        output = output.reindex(columns=original_column_names)

        #
        csv_column_names = output.columns.tolist()

        # download output data as csv file
        filename = 'prediction-items-not-procured-' + str(date.date()) + '-' + str(prediction_file_id) + '.csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

        # Write the CSV header row
        writer = csv.writer(response)
        writer.writerow(csv_column_names)

        # Write each row of data to the CSV
        for _, row in output.iterrows():
            csv_row = [row[column] for column in csv_column_names]
            writer.writerow(csv_row)

        return response


class GenerateProcuresInfoReport(APIView):
    def get(self, request, *args, **kwargs):
        is_csv_download = self.request.query_params.get('csv_download')
        contractor_alias = self.request.query_params.get('contractor')
        dt_str = self.request.query_params.get('date')
        dt_start = prepare_start_date(dt_str)
        dt_end = prepare_end_date(dt_str)

        def convert_str_to_float_or_zero(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0

        purchase_date = '{}'.format(dt_start.strftime('%Y_%m_%d'))
        data, buyers = get_procures_items_with_buyers_from_date_range(dt_start, dt_end, contractor_alias)
        if data is not None and buyers is not None:
            # Make contractors group based on buyer
            contractors = data['CONTRACTOR'].groupby(data['BY']).unique()
            incentive_rate = 0.25
            output = {
                'BUYER': [],
                'PURCHASES_TARGET': [],
                'CONTRACTOR': [],
                'UNIQUE_ITEM': [],
                'OP_UNIQUE_ITEM': [],
                'OP_BOX': [],
                'OP_VALUE': [],
                'UP_UNIQUE_ITEM': [],
                'UP_BOX': [],
                'UP_VALUE': [],
                'INCENTIVE': [],
                'TOTAL_PURCHASE': [],
                'SALES_VAL': [],
                'MARGIN': []
            }

            for buyer in buyers:
                output['BUYER'].append(buyer)
                output['CONTRACTOR'].append(contractors.loc[buyer])
                buyer_df = data[data.BY == buyer]

                purchase_value = int(buyer_df['PUR_VAL'].sum())

                output['TOTAL_PURCHASE'].append(round(purchase_value, 2))

                unique_item = len(buyer_df.ID.unique())
                output['UNIQUE_ITEM'].append(unique_item)
                op_unique_item = len(buyer_df[(buyer_df.DELTA < 0) & (buyer_df.PRE_PUR > 0)].ID.unique())
                output['OP_UNIQUE_ITEM'].append(op_unique_item)
                op_box = int(buyer_df[(buyer_df.DELTA < 0) & (buyer_df.PRE_PUR > 0)]['QTY'].sum())
                output['OP_BOX'].append(op_box)

                buyer_op = buyer_df[(buyer_df.DELTA < 0) & (buyer_df.PRE_PUR > 0)].copy()

                buyer_op['VAL'] = buyer_op['QTY'] * buyer_op['DELTA']

                op_val = int(buyer_op['VAL'].sum()) * -1
                output['OP_VALUE'].append(op_val)

                up_unique_item = len(buyer_df[(buyer_df.DELTA > 0) & (buyer_df.PRE_PUR > 0)].ID.unique())
                output['UP_UNIQUE_ITEM'].append(up_unique_item)

                up_box = int(buyer_df[(buyer_df.DELTA > 0) & (buyer_df.PRE_PUR > 0)]['QTY'].sum())
                output['UP_BOX'].append(up_box)
                incentive = int(up_box * incentive_rate)

                # Get the target purchase amount for buyer
                target_amount = convert_str_to_float_or_zero(buyer_df.iloc[0]['target_purchase'])

                # Append the result to the output
                output["PURCHASES_TARGET"].append(target_amount)

                buyer_up = buyer_df[(buyer_df.DELTA > 0) & (buyer_df.PRE_PUR > 0)].copy()
                buyer_up['VAL'] = buyer_up['QTY'] * buyer_up['DELTA']

                up_val = int(buyer_up['VAL'].sum())
                output['UP_VALUE'].append(up_val)
                output['INCENTIVE'].append(incentive)
                output['SALES_VAL'].append(round(buyer_df['SALES_VAL'].sum(), 2))
                output['MARGIN'].append(
                    round(100 * ((buyer_df['SALES_VAL'].sum() - purchase_value) / buyer_df['SALES_VAL'].sum()), 2)

                )

            if is_csv_download in ['true', 'True', 'TRUE']:
                response = HttpResponse(content_type='text/csv')
                filename = 'procures_{}.csv'.format(purchase_date)
                response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
                output_df = pd.DataFrame(output)
                contractor_df_list = output_df["CONTRACTOR"].tolist()

                for index, value in enumerate(contractor_df_list):
                    set_of_string = ','.join(map(str, value))
                    output_df.loc[index, ["CONTRACTOR"]] = set_of_string

                output_df.to_csv(response, index=False)
                return response

            output = {
                'data': output,
            }
            return Response(output, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateProcuresInfoSummary(APIView):
    def get(self, request, *args, **kwargs):
        contractor_alias = self.request.query_params.get('contractor')
        dt_str = self.request.query_params.get('date')
        dt_start = prepare_start_date(dt_str)
        dt_end = prepare_end_date(dt_str)
        data, buyers = get_procures_items_with_buyers_from_date_range(dt_start, dt_end, contractor_alias)
        if data is not None:
            filtered_data = data[data['PRE_PUR'] > 0]
            total_box = filtered_data['QTY'].sum()
            total_purchase_amount = filtered_data['PUR_VAL'].sum()
            total_sales_amount = filtered_data['SALES_VAL'].sum()

            total_profit_amount = filtered_data['TOTAL_PROFIT'].sum()
            profit_margin = (total_profit_amount / total_sales_amount) * 100

            slack_msg = "On *`{}`* total *`{}`* box medicine purchased for *`{}M`*, estimated profit is *`{}K`*, estimated margin is *`{}%`*".format(
                dt_start.strftime('%D'),
                str(round(total_box, 0)),
                str(round(total_purchase_amount / 1000000, 2)),
                str(round(total_profit_amount / 1000, 2)),
                str(round(profit_margin, 2))
            )
            context = {
                'summary': slack_msg
            }

            return Response(context, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PurchaseReportDateWise(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureItemModelSerializer.DateWisePurchaseReport

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        contructor = self.request.query_params.get("contructor", None)
        if date is None:
            date = datetime.today().date()
        # If contructor alias is passed in query params then filter by contructor
        if contructor:
            queryset = queryset.filter(
                procure__contractor__alias=contructor,
            )
        queryset = queryset.filter(
            date=date,
        ).select_related(
            "procure",
            "prediction_item",
            "procure__employee",
            "procure__supplier",
            "stock",
        ).annotate(
            PROFIT=Sum(F("prediction_item__sale_price") - F("rate")),
            DELTA=Sum(F("prediction_item__real_avg") - F("rate")),
            PUR_VAL=Sum(F("rate") * F("quantity")),
            TIME=Sum(F("procure__operation_end") - F("procure__operation_start")),
            SALES_VAL=Sum(F("quantity") * F("prediction_item__sale_price")),
            BY=Concat(F('procure__employee__first_name'), Value(' '), F('procure__employee__last_name'), output_field=CharField()),
        )

        return queryset

    def get(self, request, *args, **kwargs):
        is_csv_download = self.request.query_params.get('csv_download', None)

        if is_csv_download:
            queryset = self.get_queryset()
            if len(queryset) == 0:
                return Response(
                    {"details": "No procure purchase items found"},
                    status=status.HTTP_200_OK,
                )
            date = self.request.query_params.get("date", None)

            if date is None:
                date = datetime.today().date()

            response = create_purchase_csv_response(queryset, date)

            return response

        return super().get(request, *args, **kwargs)
