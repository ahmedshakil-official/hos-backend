import decimal
import time
from datetime import datetime, timedelta

from django.db.models import Sum, Case, When, Q, F, Value, FloatField
from django.db.models.functions import Coalesce

from common.enums import Status
from common.helpers import populate_es_index
from common.healthos_helpers import CustomerHelper
from common.utils import Round
from core.helpers import get_order_ending_time
from ecommerce.enums import ShortReturnLogType, TopSheetType
from ecommerce.models import (
    DeliverySheetItem,
    DeliverySheetInvoiceGroup,
    InvoiceGroupDeliverySheet,
    OrderInvoiceGroup,
)

from pharmacy.models import Purchase
from pharmacy.utils import get_additional_discount_data, get_discount_for_cart_and_order_items


def update_invoice_group_additional_discount_amount(queryset):
    """Update the additional discount amount for the invoice group and
    invoice group related orders
    """
    obj_to_update = []
    response_data = []
    invoice_group_ids = []
    for query in queryset:
        total_amount = float(query['total_amount'])
        discount = get_discount_for_cart_and_order_items(total_amount, rounding_off=False)

        discount_percentage = float(round(discount.get('current_discount_percentage'), 2))
        discount_amount = float(round(discount.get('current_discount_amount'), 3))
        additional_discount_rate = float(round(query['additional_discount_rate'], 2))
        additional_discount = float(round(query['additional_discount'], 3))

        if (discount_percentage != additional_discount_rate) or (discount_amount != additional_discount):
            sub_total = float(query['sub_total'])
            discount = float(query['discount'])
            additional_discount_amount = discount_amount
            total_amount = sub_total - discount - additional_discount_amount
            # based on total_amount we need to calculate the round_discount
            round_discount = round(total_amount) - total_amount

            obj_to_update.append(
                OrderInvoiceGroup(
                    id=query['id'],
                    additional_discount_rate=discount_percentage,
                    additional_discount=discount_amount,
                    round_discount=round_discount,
                )
            )
            invoice_group_ids.append(query['id'])
            order_instances = Purchase.objects.filter(
                invoice_group_id=query['id']
            )
            order_grand_total = order_instances.aggregate(
                amount_total=Coalesce(
                    Sum("amount", output_field=FloatField()) - Sum("discount", output_field=FloatField()),
                    float(0)  # Default value as Float
                )
            ).get("amount_total", float(0))
            additional_discount_data = get_additional_discount_data(
                order_grand_total,
                False,
                order_instances.first(),
            )
            for order_instance in order_instances:
                # Creating an instance of CustomerHelper with the organization ID from the order_instance
                custom_helper = CustomerHelper(order_instance.organization_id)
                # Checking if the organization has a dynamic discount factor
                if not custom_helper.has_dynamic_discount_factor():
                    # If the organization doesn't have a dynamic discount factor, then apply additional discount
                    order_instance.apply_additional_discount(
                        **additional_discount_data
                    )
            response_data.append({
                'id': query['id'],
                'total_amount': query['total_amount'],
                'additional_discount_rate': discount_percentage,
                'additional_discount': discount_amount,
            })
    OrderInvoiceGroup.objects.bulk_update(
        obj_to_update,
        ['additional_discount_rate', 'additional_discount', 'round_discount'],
        batch_size=100
    )
    populate_es_index(
        'ecommerce.models.OrderInvoiceGroup',
        {'id__in': invoice_group_ids},
    )

    return response_data


def is_last_batch_invoice_group(delivery_date: str) -> bool:
    order_ending_time = datetime.strptime(str(get_order_ending_time()),"%H:%M:%S").time()
    _delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d").date()
    start_datetime = datetime.combine(_delivery_date, order_ending_time) - timedelta(hours=1, minutes=30)
    end_datetime = datetime.combine(_delivery_date, order_ending_time) + timedelta(hours=1)
    return start_datetime <= datetime.now() <= end_datetime


def update_short_return_for_invoice_group_related_models_through_top_sheet_id(invoice_group_delivery_sheet_alias):
    from .models import InvoiceGroupDeliverySheet, DeliverySheetInvoiceGroup, DeliverySheetItem

    invoice_group_delivery_sheet = InvoiceGroupDeliverySheet.objects.only('short_amount', 'return_amount').filter(
        alias=invoice_group_delivery_sheet_alias
    )
    delivery_sheet_item_ids = invoice_group_delivery_sheet.values_list(
        'delivery_sheet_items__id', flat=True)
    delivery_sheet_invoice_group_ids = invoice_group_delivery_sheet.values_list(
        'delivery_sheet_items__delivery_sheet_invoice_groups__id', flat=True)
    delivery_sheet_items_to_update = []
    delivery_sheet_invoice_groups_to_update = []
    total_item_order = 0
    total_short_item = 0
    total_return_item = 0
    for pk in delivery_sheet_item_ids:
        delivery_sheet_item = DeliverySheetItem.objects.only('total_item_short', 'total_item_return').filter(pk=pk)
        total_return = delivery_sheet_item.aggregate(
            total_return_delivery_sheet_item=Coalesce(Sum(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then='delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__quantity'
            ), default=decimal.Decimal(0))), decimal.Decimal(0))
        )
        total_return_unique = delivery_sheet_item.filter(
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.RETURN,
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
        ).distinct(
            'delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__stock__id').count()

        total_short = delivery_sheet_item.aggregate(
            total_short_delivery_sheet_item=Coalesce(Sum(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then='delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__quantity'
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        total_short_unique = delivery_sheet_item.filter(
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.SHORT,
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE
        ).distinct(
            'delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__stock__id').count()

        total_item_order += delivery_sheet_item.values('total_item_order').get()['total_item_order']
        total_return_item += total_return['total_return_delivery_sheet_item']
        total_short_item += total_short['total_short_delivery_sheet_item']

        delivery_sheet_items_to_update.append(
            DeliverySheetItem(
                id=delivery_sheet_item.values('id').get()['id'],
                total_item_return=total_return['total_return_delivery_sheet_item'],
                total_item_short=total_short['total_short_delivery_sheet_item'],
                total_unique_item_return=total_return_unique,
                total_unique_item_short=total_short_unique,
            )
        )
    DeliverySheetItem.objects.bulk_update(
        delivery_sheet_items_to_update,
        ['total_item_return', 'total_item_short', 'total_unique_item_return', 'total_unique_item_short'],
    )
    for pk in delivery_sheet_invoice_group_ids:
        delivery_sheet_invoice_group = DeliverySheetInvoiceGroup.objects.only('total_short', 'total_return').filter(pk=pk)
        delivery_sheet_invoice_group_return = delivery_sheet_invoice_group.aggregate(
            total_return_invoice_group=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F(
                    'invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        delivery_sheet_invoice_group_short = delivery_sheet_invoice_group.aggregate(
            total_short_invoice_group=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F(
                    'invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        delivery_sheet_invoice_groups_to_update.append(
            DeliverySheetInvoiceGroup(
                id=delivery_sheet_invoice_group.values('id').get()['id'],
                total_return=delivery_sheet_invoice_group_return['total_return_invoice_group'],
                total_short=delivery_sheet_invoice_group_short['total_short_invoice_group'],
            )
        )
    DeliverySheetInvoiceGroup.objects.bulk_update(
        delivery_sheet_invoice_groups_to_update,
        ['total_return', 'total_short'],
    )

    invoice_group_delivery_sheet_return = invoice_group_delivery_sheet.aggregate(
        total_return_delivery_sheet=Coalesce(Sum(Case(When(
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
            then=F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
        ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        total_return_delivery_sheet_draft=Coalesce(Sum(Case(When(
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
            then=F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
        ), default=decimal.Decimal(0))), decimal.Decimal(0))
    )
    invoice_group_delivery_sheet_short = invoice_group_delivery_sheet.aggregate(
        total_short_delivery_sheet=Coalesce(Sum(Case(When(
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
            then=F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
        ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        total_short_delivery_sheet_draft=Coalesce(Sum(Case(When(
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
            Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
            then=F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
        ), default=decimal.Decimal(0))), decimal.Decimal(0))
    )
    invoice_group_delivery_sheet_total_data = {
        'total_order_amount': invoice_group_delivery_sheet[0].total_data['total_order_amount'],
        'total_short_amount': invoice_group_delivery_sheet_short['total_short_delivery_sheet'],
        'total_return_amount': invoice_group_delivery_sheet_return['total_return_delivery_sheet'],
        'total_short_amount_draft': invoice_group_delivery_sheet_short['total_short_delivery_sheet_draft'],
        'total_return_amount_draft': invoice_group_delivery_sheet_return['total_return_delivery_sheet_draft'],
        'total_unique_item': invoice_group_delivery_sheet[0].total_data['total_unique_item'],
        'total_item': int(total_item_order - (total_short_item + total_return_item)),
        'total_order_count': invoice_group_delivery_sheet[0].total_data['total_order_count']
    }

    invoice_group_delivery_sheet.update(
        return_amount=invoice_group_delivery_sheet_return['total_return_delivery_sheet'],
        short_amount=invoice_group_delivery_sheet_short['total_short_delivery_sheet'],
        total_data=invoice_group_delivery_sheet_total_data
    )
    msg = f"Successfully updated "
    return msg


def create_sub_sheet_name(date, responsible_employee):
    date_for_sheet_name = datetime(
            date.year, date.month, date.day
    )
    # Convert the datetime object to a string with format "YYYY-MM-DD"
    date_str = date_for_sheet_name.strftime("%Y-%m-%d")

    return responsible_employee.get_delivery_sheet_name(date_str)


def create_sub_top_sheet(top_sheet, responsible_employee):
    sub_sheet_name = create_sub_sheet_name(top_sheet.date, responsible_employee)
    sub_top_sheet = InvoiceGroupDeliverySheet.objects.create(
        name=sub_sheet_name,
        date=top_sheet.date,
        organization_id=top_sheet.organization_id,
        responsible_employee_id=responsible_employee.id,
        coordinator=responsible_employee.manager,
        query_params=top_sheet.query_params,
        filter_data=top_sheet.filter_data,
        type=TopSheetType.SUB_TOP_SHEET,
        generated_by_id=top_sheet.generated_by_id,
    )
    return sub_top_sheet


def calculate_sub_top_sheet_total_data(delivery_sheet_items_pk_list):
    delivery_sheet_item_data = DeliverySheetItem.objects.filter(
        pk__in=delivery_sheet_items_pk_list
    ).aggregate(
        total_item=Coalesce(Sum(F("total_item_order") - F("total_item_short") - F("total_item_return")), 0),
        total_order_count=Coalesce(Sum("order_count"), 0),
        total_unique_item=Coalesce(Sum("total_unique_item_order"), 0),
    )

    delivery_sheet_invoice_group_data = DeliverySheetInvoiceGroup.objects.filter(
        delivery_sheet_item__pk__in=delivery_sheet_items_pk_list
    ).aggregate(
        total_order_amount=Coalesce(Sum("grand_total"), decimal.Decimal('0.00')),
        total_short_amount=Coalesce(Sum("total_short"), decimal.Decimal('0.00')),
        total_return_amount=Coalesce(Sum("total_return"), decimal.Decimal('0.00')),
    )
    total_data = {
        "total_item": delivery_sheet_item_data.get("total_item"),
        "total_order_count": delivery_sheet_item_data.get("total_order_count"),
        "total_unique_item": delivery_sheet_item_data.get("total_unique_item"),
        "total_order_amount": delivery_sheet_invoice_group_data.get("total_order_amount"),
        "total_short_amount": delivery_sheet_invoice_group_data.get("total_short_amount"),
        "total_return_amount": delivery_sheet_invoice_group_data.get("total_return_amount"),
    }

    return total_data

def assign_delivery_items_and_delivery_sheet_invoice_groups_to_sub_to_sheet(
    delivery_sheet_items_pk_list,
    sub_top_sheet_id,
    ):
    DeliverySheetItem.objects.filter(pk__in=delivery_sheet_items_pk_list).update(
        invoice_group_delivery_sub_sheet_id=sub_top_sheet_id
    )


def update_sub_top_sheet_related_data(invoice_group_delivery_sub_sheet_id, instance_type):
    """take a sub top sheet id and update short/return related data

    Args:
        invoice_group_delivery_sub_sheet_id (int): sub_sheet_id
        instance_type (int): type enum short/return

    Returns:
        _type_: _description_
    """
    total_data_to_be_updated = {}
    data_to_be_updated = {}

    invoice_group_delivery_sub_sheet = InvoiceGroupDeliverySheet.objects.only(
        'short_amount',
        'return_amount',
        'total_data',
    ).filter(
        pk=invoice_group_delivery_sub_sheet_id
    )

    delivery_sheet_item_data = DeliverySheetItem.objects.filter(
        invoice_group_delivery_sub_sheet__id=invoice_group_delivery_sub_sheet_id
    ).aggregate(
        total_item=Coalesce(Sum(F("total_item_order") - F("total_item_short") - F("total_item_return")), 0),
        total_order_count=Coalesce(Sum("order_count"), 0),
        # total_unique_item=Coalesce(Sum(F("total_unique_item_order") - F("total_unique_item_short") - F("total_unique_item_return")), 0),
        total_unique_item=Coalesce(Sum("total_unique_item_order"), 0),
    )
    total_data_to_be_updated["total_item"] = float(delivery_sheet_item_data.get("total_item", 0))
    total_data_to_be_updated["total_order_count"] = float(delivery_sheet_item_data.get("total_order_count", 0))
    total_data_to_be_updated["total_unique_item"] = float(delivery_sheet_item_data.get("total_unique_item", 0))

    invoice_group_delivery_sub_sheet_short_return = invoice_group_delivery_sub_sheet.aggregate(
        total_short_return_delivery_sheet=Coalesce(Sum(Case(When(
            Q(sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=instance_type) &
            Q(sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
            then=F('sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
        ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        total_short_return_delivery_sheet_draft=Coalesce(Sum(Case(When(
            Q(sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=instance_type) &
            Q(sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
            then=F('sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
        ), default=decimal.Decimal(0))), decimal.Decimal(0))
    )

    if instance_type == ShortReturnLogType.RETURN:
        data_to_be_updated["return_amount"] = float(invoice_group_delivery_sub_sheet_short_return.get('total_short_return_delivery_sheet', 0))
        total_data_to_be_updated["total_return_amount"] = float(invoice_group_delivery_sub_sheet_short_return.get('total_short_return_delivery_sheet', 0))
        total_data_to_be_updated["total_return_amount_draft"] = float(invoice_group_delivery_sub_sheet_short_return.get('total_short_return_delivery_sheet_draft', 0))
    elif instance_type == ShortReturnLogType.SHORT:
        data_to_be_updated["short_amount"] = float(invoice_group_delivery_sub_sheet_short_return.get('total_short_return_delivery_sheet', 0))
        total_data_to_be_updated["total_short_amount"] = float(invoice_group_delivery_sub_sheet_short_return.get('total_short_return_delivery_sheet', 0))
        total_data_to_be_updated["total_short_amount_draft"] = float(invoice_group_delivery_sub_sheet_short_return.get('total_short_return_delivery_sheet_draft', 0))

    total_data = invoice_group_delivery_sub_sheet.get().total_data
    total_data.update(total_data_to_be_updated)
    data_to_be_updated["total_data"] = total_data
    invoice_group_delivery_sub_sheet.update(
        **data_to_be_updated
    )


def get_dynamic_discount_message(discount_percentage):
    if float(discount_percentage) > 0:
        message = f"""আপনার গত ১৪ দিনের পণ্য ক্রয়ের উপর ভিত্তি করে আপনার ইনভয়েসে <b>{discount_percentage}%</b> ডিসকাউন্ট দেয়া হয়েছে, যা পণ্যের মূল্যের সাথে সমন্বয় করা আছে, আরো বেশি কেনা কাটা করে আরো বেশি ডিসকাউন্ট পান।"""
    else:
        message = """আপনার গত ১৪ দিনের পণ্য ক্রয়ের উপর ভিত্তি করে আপনার ডিসকাউন্ট সেট হয় এবং পণ্যের মূল্যের সাথে সমন্বয় করা হয়, আরো বেশি কেনা কাটা করে আরো বেশি ডিসকাউন্ট পান।"""
    return message
