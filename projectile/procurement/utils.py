from __future__ import division

import logging
import contextlib
import csv
from datetime import timedelta, datetime
from decimal import Decimal
from validator_collection import checkers
from simple_history.utils import bulk_update_with_history

import pandas as pd

from django.http import HttpResponse

from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from common.enums import Status

from procurement.enums import ProcureDateUpdateType, ReturnCurrentStatus

DECIMAL_ZERO = Decimal("0.000")

logger = logging.getLogger(__name__)


def get_procures_items_with_buyers_from_date_range(dt_start, dt_end, contractor_alias=None):
    from procurement.models import Procure, ProcureItem, PredictionItem

    with contextlib.suppress(AttributeError):
        contractor_alias_list = contractor_alias.split(",")

    if contractor_alias:
        filters = {
            "date__lte": dt_end,
            "date__gte": dt_start,
            "status": Status.ACTIVE,
            "procure__contractor__alias__in": contractor_alias_list
        }
    else:
        filters = {
            "date__lte": dt_end,
            "date__gte": dt_start,
            "status": Status.ACTIVE
        }

    data = ProcureItem.objects.filter(
        **filters
    ).values(
        'stock__id',
        'procure',
        'procure__employee__id',
        'procure__employee__first_name',
        'procure__employee__last_name',
        'procure__contractor__first_name',
        'procure__contractor__last_name',
        'procure__supplier__company_name',
        'product_name',
        'company_name',
        'rate',
        'quantity',
        'prediction_item__sale_price',
        'prediction_item__avg_purchase_rate',
        # 'entry_by__first_name',
        # 'entry_by__last_name',
        'procure__operation_start',
        'procure__operation_end',
        'prediction_item__worst_rate',
        'prediction_item__avg_purchase_rate',
        'prediction_item__real_avg',
        'prediction_item__lowest_purchase_rate',
        'prediction_item__suggested_purchase_quantity',
        'prediction_item__suggested_min_purchase_quantity',
    )

    prediction_item_assign_to_ids = list(set(data.values_list("procure__employee__id", flat=True)))

    prediction_items = PredictionItem().get_all_actives().filter(
        assign_to__in=prediction_item_assign_to_ids,
        date=dt_start.date(),
    ).values(
        "suggested_purchase_quantity",
        "avg_purchase_rate",
        "assign_to__id"
    )
    prediction_item_df = pd.DataFrame(
        prediction_items,
        columns=["suggested_purchase_quantity", "avg_purchase_rate", "assign_to__id"]
    )
    data = pd.DataFrame(data)

    #Calculate buyer target purchase and merge with data
    buyer_target_purchase = (
        prediction_item_df
        .assign(target_purchase=prediction_item_df['suggested_purchase_quantity'] * prediction_item_df['avg_purchase_rate'])
        .groupby('assign_to__id')['target_purchase']
        .sum()
        .reset_index()
    )
    # Create an empty 'procure__employee__id' column if it doesn't exist to solve key error issue
    if 'procure__employee__id' not in data.columns:
        data['procure__employee__id'] = None

    # Merge the target purchase value for each buyer
    data = data.merge(buyer_target_purchase, left_on="procure__employee__id", right_on="assign_to__id", how="left")

    if not data.empty:
        data['BY'] = data['procure__employee__first_name'] + ' ' + data['procure__employee__last_name']

        data['CONTRACTOR'] = data['procure__contractor__first_name'] + ' ' + data['procure__contractor__last_name']

        data = data.rename(columns={
            'stock__id': 'ID',
            'procure__supplier__company_name': 'SUPPLIER',
            'product_name': 'PRODUCT',
            'company_name': 'COM',
            'prediction_item__sale_price': 'SALES',
            'quantity': 'QTY',
            'prediction_item__real_avg': 'PRE_PUR',
            'rate': 'PUR',
            'procure__operation_start': 'OP_START',
            'procure__operation_end': 'OP_END',
            'prediction_item__worst_rate': 'WORST_RATE',
            'prediction_item__avg_purchase_rate': 'BEST_RATE',
            'prediction_item__suggested_purchase_quantity': 'D3',
            'prediction_item__suggested_min_purchase_quantity': 'D1'
        })
        data['PROFIT'] = data['SALES'] - data['PUR']
        data['DELTA'] = data['PRE_PUR'] - data['PUR']
        data['TOTAL_PROFIT'] = data['PROFIT'] * data['QTY']
        data['PUR_VAL'] = data['PUR'] * data['QTY']
        data['TIME'] = data['OP_END'] - data['OP_START']
        data['SALES_VAL'] = data['QTY'] * data['SALES']

        data.drop(
            [
                "procure__employee__first_name",
                "procure__employee__last_name",
                "OP_START",
                "OP_END",
                "procure__contractor__first_name",
                "procure__contractor__last_name",
                "procure__employee__id",
                "assign_to__id",
            ],
            inplace=True,
            axis=1,
        )

        # Fill missing values with an empty string
        data.fillna('', inplace=True)

        buyers = data.BY.unique()
        # replace with '-' if no contractor in the procure data
        data['CONTRACTOR'] = data['CONTRACTOR'].fillna('-')

        return data, buyers

    return None, None


def convert_timedelta_to_dhms(time_delta):
    """This method take time delta object and returns day hour minute and seconds"""
    days = time_delta.days
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} days {hours:02d}:{minutes:02d}:{seconds:02d}"


def create_purchase_csv_response(queryset, date):
    filename = 'procures_purchase_{}.csv'.format(date)
    # Define the CSV headers
    headers = [
            'Id',
            'procure',
            'SUPPLIER',
            'PRODUCT',
            'COM',
            'PUR',
            'QTY',
            'SALES',
            'BEST_RATE',
            'WORST_RATE',
            'PRE_PUR',
            'prediction_item__lowest_purchase_rate',
            'D3',
            'D1',
            'BY',
            'PROFIT',
            'DELTA',
            'TOTAL_PROFIT',
            'PUR_VAL',
            'TIME',
            'SALES_VAL',
        ]

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    writer = csv.writer(response)
    writer.writerow(headers)
    # Write items row wise in csv file
    for item in queryset:
        time_in_dhms = convert_timedelta_to_dhms(item.TIME)
        row = [
            item.stock_id,
            item.procure_id,
            item.procure.supplier.company_name,
            item.product_name,
            item.company_name,
            item.rate,
            item.quantity,
            item.prediction_item.sale_price,
            item.prediction_item.avg_purchase_rate,
            item.prediction_item.worst_rate,
            item.prediction_item.real_avg,
            item.prediction_item.lowest_purchase_rate,
            item.prediction_item.suggested_purchase_quantity,
            item.prediction_item.suggested_min_purchase_quantity,
            item.BY,
            item.PROFIT,
            item.DELTA,
            item.PROFIT * item.quantity,
            item.PUR_VAL,
            time_in_dhms,
            item.SALES_VAL,
        ]
        writer.writerow(row)

    return response


def calculate_total_settled_amount(procure_return):
    from procurement.models import ReturnSettlement
    """This function calculate total settled amount
    and change the procure return current status based on amount
    """
    total_settled_amount = (
        ReturnSettlement()
        .get_all_actives()
        .filter(procure_return_id=procure_return.id)
        .aggregate(
            total_settled_amount=Coalesce(
                Sum("amount"), Value(0, output_field=DecimalField())
            )
        )["total_settled_amount"]
    )

    procure_return.total_settled_amount = total_settled_amount
    if total_settled_amount < 1:
        procure_return.current_status = ReturnCurrentStatus.PENDING
        procure_return.full_settlement_date = None
    elif procure_return.total_return_amount == total_settled_amount:
        procure_return.current_status = ReturnCurrentStatus.SETTLED
        procure_return.full_settlement_date = timezone.now()
    elif procure_return.total_return_amount > total_settled_amount:
        procure_return.current_status = ReturnCurrentStatus.PARTIALLY_SETTLED
        procure_return.full_settlement_date = None

    procure_return.save(update_fields=["current_status", "total_settled_amount", "full_settlement_date"])

    return procure_return


def calculate_procurement_procure_data(procure_instance):
    logger.info("procurement>>utils: Calculating credit_payment_term_date, credit_cost_amount, open_credit_balance")

    if procure_instance.date and procure_instance.credit_payment_term:
        # calculating credit payment term date based on purchase_date and credit_payment_term_date
        procure_instance.credit_payment_term_date = procure_instance.date + timedelta(days=procure_instance.credit_payment_term)

    if procure_instance.credit_amount and procure_instance.credit_cost_percentage:
        # calculating credit cost amount based on credit amount and credit cost percentage
        procure_instance.credit_cost_amount = procure_instance.credit_amount * Decimal(procure_instance.credit_cost_percentage / 100)

    if procure_instance.credit_amount and procure_instance.paid_amount:
        # calculate open credit balance based on credit amount and paid amount
        procure_instance.open_credit_balance = procure_instance.credit_amount - procure_instance.paid_amount

    procure_instance.save(update_fields=["credit_payment_term_date", "credit_cost_amount", "open_credit_balance"])

    return procure_instance


def calculate_procurement_procure_group_data(procure_group):
    logger.info("procurement>>utils: Calculating credit_payment_term_date, credit_cost_amount, open_credit_balance")

    if procure_group.date and procure_group.credit_payment_term:
        # calculating credit payment term date based on purchase_date and credit_payment_term_date
        procure_group.credit_payment_term_date = timezone.now().date() + timedelta(days=procure_group.credit_payment_term)

    # calculating credit cost amount based on credit amount and credit cost percentage
    credit_cost_amount = procure_group.credit_amount * Decimal(procure_group.credit_cost_percentage / 100)
    procure_group.credit_cost_amount = credit_cost_amount

    # calculate open credit balance based on credit amount and paid amount
    open_credit_balance = (procure_group.credit_amount + credit_cost_amount) - procure_group.paid_amount
    procure_group.open_credit_balance = open_credit_balance

    procure_group.save(update_fields=["credit_payment_term_date", "credit_cost_amount", "open_credit_balance"])

    return procure_group


def calculate_procure_payment_data(procure_instance):
    """This method calculated total paid amount
    and update the open_credit_balance for that procure."""
    from procurement.models import ProcurePayment

    total_paid_amount = (
        ProcurePayment()
        .get_all_actives()
        .filter(procure_id=procure_instance.id)
        .aggregate(
            total_paid_amount=Coalesce(
                Sum("amount"), Value(0, output_field=DecimalField())
            )
        )
    )["total_paid_amount"]

    _open_credit_balance = Decimal(procure_instance.credit_amount) - Decimal(total_paid_amount)
    procure_instance.paid_amount = total_paid_amount
    procure_instance.open_credit_balance = _open_credit_balance
    procure_instance.save(update_fields=["paid_amount", "open_credit_balance"])

    # Logging the information
    logger.info(
        f"Payment data updated for Procure ID {procure_instance.id}. "
        f"Total Paid Amount: {total_paid_amount}, "
        f"Open Credit Balance: {_open_credit_balance}"
    )

    return procure_instance


def calculate_procure_group_payment_data(procure_group):
    """This method calculated total paid amount
    and update the open_credit_balance for that procure group."""
    from procurement.models import ProcurePayment

    total_paid_amount = (
        ProcurePayment()
        .get_all_actives()
        .filter(procure_group_id=procure_group.id)
        .aggregate(
            total_paid_amount=Coalesce(
                Sum("amount"), Value(0, output_field=DecimalField())
            )
        )
    )["total_paid_amount"]

    if total_paid_amount:
        _open_credit_balance = Decimal(procure_group.credit_amount + procure_group.credit_cost_amount) - Decimal(total_paid_amount)
        procure_group.paid_amount = total_paid_amount
        procure_group.open_credit_balance = _open_credit_balance
        procure_group.save(update_fields=["paid_amount", "open_credit_balance"])

        # Logging the information
        logger.info(
            f"Payment data updated for Procure ID {procure_group.id}. "
            f"Total Paid Amount: {total_paid_amount}, "
            f"Open Credit Balance: {_open_credit_balance}"
        )

    return procure_group


def get_updated_by_data(user):
    return {
        "id": user.id,
        "alias": user.alias,
        "first_name": f"{user.first_name}",
        "last_name": f"{user.last_name}",
        "phone": f"{user.phone}",
        "code": f"{user.code}",
    }


def update_procures_credit(validated_data):
    from rest_framework.exceptions import ValidationError
    from .models import Procure

    procure_needs_to_be_updated = {}

    new_credit_payment_term = validated_data.get("credit_payment_term")
    new_credit_cost_percentage = validated_data.get("credit_cost_percentage")
    procures = validated_data.get("procures")

    for procure in procures:
        alias = procure.get("alias")
        credit_amount = procure.get("credit_amount")

        procure_needs_to_be_updated[alias] = {
            "alias": alias,
            "credit_amount": credit_amount,
        }

    procure_aliases = list(procure_needs_to_be_updated.keys())
    queryset = Procure.objects.filter(alias__in=procure_aliases)

    if not queryset.exists():
        raise ValidationError(
            {
                "detail": "No procures found to update. Please provide valid procure items."
            }
        )
    if len(queryset) != len(procure_aliases):
        raise ValidationError({"detail": "Few procures are missing to update."})

    """
    Generate error for each procure if updating/new credit amount is greater than sub total
    or less than paid amount
    """
    error = {}

    for procure_instance in queryset:
        id = procure_instance.id
        alias = procure_instance.alias
        sub_total = procure_instance.sub_total
        paid_amount = procure_instance.paid_amount
        new_credit_amount = procure_needs_to_be_updated[alias].get("credit_amount")

        if new_credit_amount > sub_total:
            error[id] = {
                "id": id,
                "alias": alias,
                "credit_amount": "Credit amount can not be greater than sub total.",
            }
            continue

        if new_credit_amount < paid_amount:
            error[id] = {
                "id": id,
                "alias": alias,
                "credit_amount": f"Credit amount can not be less than paid amount, already paid BDT - {paid_amount}.",
            }

        if new_credit_amount == DECIMAL_ZERO:
            procure_instance.is_credit_purchase = False
            procure_instance.credit_amount = DECIMAL_ZERO
            procure_instance.credit_cost_percentage = DECIMAL_ZERO
            procure_instance.credit_cost_amount = DECIMAL_ZERO
            procure_instance.open_credit_balance = DECIMAL_ZERO
            procure_instance.credit_payment_term = 0
            procure_instance.credit_payment_term_date = None
            procure_instance.paid_amount = DECIMAL_ZERO
        else:
            procure_instance.is_credit_purchase = True
            procure_instance.credit_amount = new_credit_amount
            procure_instance.credit_cost_percentage = new_credit_cost_percentage
            procure_instance.credit_cost_amount = (new_credit_amount * new_credit_cost_percentage) / 100
            procure_instance.open_credit_balance = new_credit_amount - paid_amount
            procure_instance.credit_payment_term = new_credit_payment_term
            procure_instance.credit_payment_term_date = procure_instance.date + timedelta(days=new_credit_payment_term)

    if error:
        raise ValidationError(list(error.values()))

    # If no errors generated, then update all the procures with new credit amount and related fields
    bulk_update_with_history(queryset, Procure, ["is_credit_purchase", "credit_amount", "credit_cost_percentage", "credit_cost_amount", "open_credit_balance", "credit_payment_term", "credit_payment_term_date", "paid_amount"])


def get_procure_update_date(date, date_update_type):
    if date_update_type == ProcureDateUpdateType.ADVANCE:
        date = date + timezone.timedelta(days=1)
    else:
        date = date - timezone.timedelta(days=1)
    return date


def generate_credit_report_csv_response(queryset):
    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    filename = f"credit_report{datetime.today().date()}.csv"
    response['Content-Disposition'] = f"attachment; filename={filename}"

    csv_writer = csv.writer(response)

    # Write the header row
    csv_writer.writerow([
        "ID",
        "Supplier",
        "Contractor",
        "Procures",
        "Invoices",
        "Requisition",
        "total_amount",
        "total_discount",
        "credit_amount",
        "paid_amount",
        "credit_payment_term",
        "credit_payment_term_date",
        "credit_cost_percentage",
        "credit_cost_amount",
        "open_credit_balance",
        "cash_commission",
        "total_paid_amount",
        "total_credit_amount",
        "total_open_credit_balance",
        "credit_status"
    ])

    # Write data rows
    for row in queryset:
        if pd.notna(row.supplier) is True:
            supplier_name = f"{row.supplier.first_name} {row.supplier.last_name}"
            supplier = (
                f"Name: {row.supplier.first_name} {row.supplier.last_name} - ID: {row.supplier.id}"
                if supplier_name != " "
                else f"ID: {row.supplier.id}"
            )
        else:
            supplier = ""

        contractor = row.contractor if pd.notna(row.contractor) else "-"

        if pd.notna(row.contractor) is True:
            contractor = (
                f"Name: {contractor.first_name} {contractor.last_name} - ID: {contractor.id}"
                if f"Name: {contractor.first_name} {contractor.last_name} - ID: {contractor.id}" != " "
                else f"ID: {contractor.id}"
            )
        else:
            contractor = ""

        if None not in row.invoices:
            invoices = ', '.join(row.invoices)
        else:
            invoices = ""

        if pd.notna(row.requisition) is True:
            requisition = row.requisition_id
        else:
            requisition = ""

        procures = ""
        for procure in row.procures:
            procures += f"{str(procure.id)},"

        csv_writer.writerow([
            row.id,
            supplier,
            contractor,
            procures,
            invoices,
            requisition,
            row.total_amount,
            row.total_discount,
            row.credit_amount,
            row.paid_amount,
            row.credit_payment_term,
            row.credit_payment_term_date,
            row.credit_cost_percentage,
            row.credit_cost_amount,
            row.open_credit_balance,
            row.cash_commission,
            row.total_paid_amount,
            row.total_credit_amount,
            row.total_open_credit_balance,
            row.credit_status
        ])

    return response
