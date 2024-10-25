import logging, decimal

from django.db.models import Sum, Case, When, Q, F
from django.db.models.functions import Coalesce

from common.enums import Status
from common.helpers import send_log_alert_to_slack_or_mattermost, populate_es_index
from common.helpers import custom_elastic_rebuild
from common.utils import Round
from pharmacy.tasks import apply_additional_discount_on_order
from .enums import ShortReturnLogType
from projectile.celery import app


logger = logging.getLogger(__name__)


@app.task
def send_push_notification_on_short(invoice_group_id, entry_by_id):
    from ecommerce.models import OrderInvoiceGroup

    order_invoice_group = OrderInvoiceGroup.objects.only('id').get(pk=invoice_group_id)
    order_invoice_group.send_push_notification_on_short(entry_by_id)

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_es_index_for_related_invoices(invoice_id_list):
    from ecommerce.models import OrderInvoiceGroup

    invoices = OrderInvoiceGroup.objects.only('id').filter(pk__in=invoice_id_list)
    for invoice in invoices:
        related_invoices = invoice.related_invoice_groups(pk_list = True)
        if related_invoices.exists():
            custom_elastic_rebuild(
                'ecommerce.models.OrderInvoiceGroup',
                {'pk__in': list(related_invoices)}
            )


@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_short_and_return_for_invoice(invoice_group_id, instance_type):
    from ecommerce.models import OrderInvoiceGroup

    invoice_group = OrderInvoiceGroup.objects.only(
        'total_short',
        'total_return',
        'sub_total',
        'discount',
        'additional_discount',
        'round_discount',
        'additional_cost',
    ).get(pk=invoice_group_id)

    if instance_type == ShortReturnLogType.RETURN:
        invoice_group.total_return = invoice_group.return_total
        invoice_group.save(update_fields=['total_return', ])
    elif instance_type == ShortReturnLogType.SHORT:
        invoice_group.total_short = invoice_group.short_total
        invoice_group.save(update_fields=['total_short', ])

    # calculating Grand Total
    grand_total = (
        invoice_group.sub_total
        - invoice_group.discount
        + invoice_group.round_discount
        - invoice_group.additional_discount
        + invoice_group.additional_cost
        - invoice_group.total_short
        - invoice_group.total_return
    )

    # if grand total is 0 or short + return amount is less or equal to 0 then set additional discount to 0
    if grand_total <= 0:
        additional_discount_value_zero = 0
        invoice_group.additional_discount = additional_discount_value_zero
        invoice_group.save()
        logger.info(f"Additional Discount Set to Zero for OrderInvoiceGroup ID: {invoice_group_id}")


# This task is for tracking an issue
@app.task
def send_invoice_status_change_log_to_mm(
    order_invoice_group_ids, responsible_employee, tracking_status, entry_by_id, _timestamp):
    from ecommerce.models import OrderInvoiceGroup

    _list =order_invoice_group_ids
    number_of_key = len(_list)
    index = 0
    chunk_size = 50

    while index < number_of_key:
        new_index = index + chunk_size
        invoice_groups = list(OrderInvoiceGroup.objects.filter(
            pk__in=_list[index: new_index],
        ).extra(select={"delivery_date": "to_char( delivery_date, 'YYYY-MM-DD' )"}).values_list(
            "pk",
            "delivery_date",
        ))
        index = new_index

        data = {
            "inv": invoice_groups,
            "dm": responsible_employee,
            "status": tracking_status,
            "uid": entry_by_id,
            "time": _timestamp
        }
        data = str(data)
        send_log_alert_to_slack_or_mattermost(data)


@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_short_and_return_for_invoice_group_related_models(
    delivery_sheet_invoice_group_id,
    delivery_sheet_item_id,
    invoice_group_delivery_sheet_id,
    invoice_group_delivery_sub_sheet_id,
    instance_type,
    ):
    from ecommerce.models import (
        DeliverySheetInvoiceGroup,
        InvoiceGroupDeliverySheet,
        DeliverySheetItem,
    )
    from .utils import update_sub_top_sheet_related_data
    delivery_sheet_invoice_group = DeliverySheetInvoiceGroup.objects.only('total_short', 'total_return').filter(
        pk=delivery_sheet_invoice_group_id)
    invoice_group_delivery_sheet = InvoiceGroupDeliverySheet.objects.only('short_amount', 'return_amount').filter(
        pk=invoice_group_delivery_sheet_id)
    delivery_sheet_item = DeliverySheetItem.objects.only('total_item_short', 'total_item_return').filter(
        pk=delivery_sheet_item_id
    )
    logger.info("Instance type: %s", instance_type)
    if instance_type == ShortReturnLogType.RETURN:
        delivery_sheet_item_total_return = delivery_sheet_item.aggregate(
            total_return_delivery_sheet_item=Coalesce(Sum(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then='delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__quantity'
            ), default=decimal.Decimal(0))), decimal.Decimal(0))
        )
        total_return_unique_delivery_sheet_item = delivery_sheet_item.filter(
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.RETURN,
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
        ).distinct(
            'delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__stock__id').count()
        invoice_group_delivery_sheet_return = invoice_group_delivery_sheet.aggregate(
            total_return_delivery_sheet=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_return_delivery_sheet_draft=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0))
        )
        delivery_sheet_invoice_group_return = delivery_sheet_invoice_group.aggregate(
            total_return_invoice_group=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F('invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        total_item = DeliverySheetItem.objects.filter(
            invoice_group_delivery_sheet__id=invoice_group_delivery_sheet_id
        ).aggregate(
            total_item=Coalesce(Sum(F("total_item_order") - F("total_item_short") - F("total_item_return")), 0),
        ).get("total_item")
        # get total ordered and short return items for this delivery sheet
        # total_item_order = delivery_sheet_item.values('total_item_order').get()['total_item_order']
        # total_short_and_return_item = delivery_sheet_item_total_return['total_return_delivery_sheet_item'] + delivery_sheet_item.values('total_item_short').get()['total_item_short']
        # In total data for InvoiceGroupDeliverySheet, Here we only change total_return_amount and total_item
        invoice_group_delivery_sheet_total_data = {
            'total_order_amount': invoice_group_delivery_sheet[0].total_data['total_order_amount'],
            'total_short_amount': invoice_group_delivery_sheet[0].total_data['total_short_amount'],
            'total_return_amount': invoice_group_delivery_sheet_return['total_return_delivery_sheet'],
            'total_return_amount_draft': invoice_group_delivery_sheet_return['total_return_delivery_sheet_draft'],
            'total_unique_item': invoice_group_delivery_sheet[0].total_data['total_unique_item'],
            'total_item': int(total_item),
            'total_order_count': invoice_group_delivery_sheet[0].total_data['total_order_count']
        }

        delivery_sheet_invoice_group.update(total_return=delivery_sheet_invoice_group_return['total_return_invoice_group'])
        invoice_group_delivery_sheet.update(
            return_amount=invoice_group_delivery_sheet_return['total_return_delivery_sheet'],
            total_data=invoice_group_delivery_sheet_total_data
        )
        delivery_sheet_item.update(
            total_item_return=delivery_sheet_item_total_return['total_return_delivery_sheet_item'],
            total_unique_item_return=total_return_unique_delivery_sheet_item
        )

    elif instance_type == ShortReturnLogType.SHORT:
        total_item_short = delivery_sheet_item.aggregate(
            total_short_delivery_sheet_item=Coalesce(Sum(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then='delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__quantity'
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        total_short_unique_delivery_sheet_item = delivery_sheet_item.filter(
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.SHORT,
            delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE
        ).distinct(
            'delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__stock__id').count()

        invoice_group_delivery_sheet_short = invoice_group_delivery_sheet.aggregate(
            total_short_delivery_sheet=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_short_delivery_sheet_draft=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0))
        )
        delivery_sheet_invoice_group_short = delivery_sheet_invoice_group.aggregate(
            total_short_invoice_group=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F('invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        total_item = DeliverySheetItem.objects.filter(
            invoice_group_delivery_sheet__id=invoice_group_delivery_sheet_id
        ).aggregate(
            total_item=Coalesce(Sum(F("total_item_order") - F("total_item_short") - F("total_item_return")), 0),
        ).get("total_item")
        # get total ordered and short return items for this delivery sheet
        # total_item_order = delivery_sheet_item.values('total_item_order').get()['total_item_order']
        # In total data for InvoiceGroupDeliverySheet, Here we only change total_short_amount and total_item
        # total_short_and_return_item = total_item_short['total_short_delivery_sheet_item'] + delivery_sheet_item.values('total_item_return').get()['total_item_return']
        invoice_group_delivery_sheet_total_data = {
            'total_order_amount': invoice_group_delivery_sheet[0].total_data['total_order_amount'],
            'total_short_amount': invoice_group_delivery_sheet_short['total_short_delivery_sheet'],
            'total_short_amount_draft': invoice_group_delivery_sheet_short['total_short_delivery_sheet_draft'],
            'total_return_amount': invoice_group_delivery_sheet[0].total_data['total_return_amount'],
            'total_unique_item': invoice_group_delivery_sheet[0].total_data['total_unique_item'],
            'total_item': int(total_item),
            'total_order_count': invoice_group_delivery_sheet[0].total_data['total_order_count']
        }

        delivery_sheet_invoice_group.update(total_short=delivery_sheet_invoice_group_short['total_short_invoice_group'])
        invoice_group_delivery_sheet.update(
            short_amount=invoice_group_delivery_sheet_short['total_short_delivery_sheet'],
            total_data=invoice_group_delivery_sheet_total_data
        )
        delivery_sheet_item.update(
            total_item_short=total_item_short['total_short_delivery_sheet_item'],
            total_unique_item_short=total_short_unique_delivery_sheet_item
        )
    # Update short data for sub top sheet
    if invoice_group_delivery_sub_sheet_id:
        update_sub_top_sheet_related_data(
            invoice_group_delivery_sub_sheet_id=invoice_group_delivery_sub_sheet_id,
            instance_type=instance_type
        )



@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_invoice_groups_additional_discount_based_on_delivery_date(invoice_group_date_list):
    from .models import OrderInvoiceGroup
    from pharmacy.utils import get_minimum_order_amount
    from .utils import update_invoice_group_additional_discount_amount

    minimum_order_amount = get_minimum_order_amount()
    # get unique values from invoice_group_date_list just for caution
    invoice_group_date_list = list(set(invoice_group_date_list))

    queryset = OrderInvoiceGroup.objects.filter(
        delivery_date__in=invoice_group_date_list,
    ).annotate(
        total_amount=Coalesce(Round(F('sub_total') - F('discount')), decimal.Decimal(0)),
    ).filter(
        total_amount__gte=minimum_order_amount,
    ).values(
        'id',
        'orders__id',
        'sub_total',
        'discount',
        'total_amount',
        'additional_discount',
        'additional_discount_rate'
    )
    response_data = update_invoice_group_additional_discount_amount(queryset)
    invoice_group_ids = list(map(lambda x: x['id'], response_data))
    logger.info('Updated additional discount for invoice groups ==> IDs:{}'.format(invoice_group_ids))
