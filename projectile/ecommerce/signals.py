import logging
import datetime
import json
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import Coalesce

from common.utils import Round
from common.enums import Status
from common.helpers import (
    custom_elastic_rebuild,
    send_top_sheet_activity_alert_to_slack_or_mattermost,
)

from pharmacy.models import Purchase
from pharmacy.utils import (
    send_push_notification_for_additional_discount,
)
from pharmacy.tasks import fix_stock_on_mismatch_and_send_log_to_mm

from .enums import ShortReturnLogType
from .tasks import update_short_and_return_for_invoice, update_short_and_return_for_invoice_group_related_models


logger = logging.getLogger(__name__)


@transaction.atomic
def pre_save_short_return_item(sender, instance, **kwargs):
    if instance._state.adding:
        if instance.type == ShortReturnLogType.RETURN and instance.status == Status.ACTIVE:
            instance.stock.refresh_from_db(fields=('ecom_stock',))
            instance.stock.ecom_stock += float(instance.quantity)
            instance.stock.save(update_fields=['ecom_stock', 'orderable_stock',])
            # Celery Task: Fix stock on mismatch
            # fix_stock_on_mismatch_and_send_log_to_mm.apply_async(
            #     (instance.stock_id, ),
            #     countdown=5,
            #     retry=True, retry_policy={
            #         'max_retries': 10,
            #         'interval_start': 0,
            #         'interval_step': 0.2,
            #         'interval_max': 0.2,
            #     }
            # )
    else:
        old_instance = sender.objects.get(pk=instance.id)
        if old_instance.status == Status.DRAFT and instance.status == Status.ACTIVE and instance.type == ShortReturnLogType.RETURN:
            instance.stock.refresh_from_db(fields=('ecom_stock',))
            instance.stock.ecom_stock += float(instance.quantity)
            instance.stock.save(update_fields=['ecom_stock', 'orderable_stock',])


@transaction.atomic
def pre_save_short_return_log(sender, instance, **kwargs):
    if not instance._state.adding:
        old_instance = sender.objects.get(pk=instance.id)
        if (old_instance.status == Status.DRAFT and instance.status == Status.ACTIVE) or (
                old_instance.status in [Status.ACTIVE, Status.DRAFT] and instance.status == Status.INACTIVE):
            instance.change_short_return_items_status(
                previous_status=old_instance.status,
                current_status=instance.status,
            )
        update_short_and_return_for_invoice.apply_async(
            (instance.invoice_group_id, instance.type,),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
    else:
        if instance.status == Status.ACTIVE:
            update_short_and_return_for_invoice.apply_async(
                (instance.invoice_group_id, instance.type,),
                countdown=5,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )

    custom_elastic_rebuild(
        'ecommerce.models.OrderInvoiceGroup',
        {'pk': instance.invoice_group_id}
    )
    custom_elastic_rebuild(
        'pharmacy.models.Purchase',
        {'pk': instance.order_id}
    )
    # Expire order list cache
    instance.order.expire_cache()


def post_save_short_return_log(sender, instance, created, **kwargs):
    from .models import DeliverySheetInvoiceGroup
    from .models import ShortReturnLog
    # if created:
    #     short_return_instance = ShortReturnLog.objects.filter(
    #         pk=instance.id
    #     )
    #     short_return_amount = short_return_instance.filter(
    #         invoice_group__invoice_groups__status__in=[Status.ACTIVE, Status.DRAFT]
    #     ).aggregate(
    #         total_amount=Sum('invoice_group__invoice_groups__short_return_amount')
    #     ).get('total_amount', Decimal(0))
    #     invoice_amount = short_return_instance.aggregate(
    #         total_amount=Sum('invoice_group__sub_total') - Sum('invoice_group__discount')
    #     ).get('total_amount', Decimal(0))
    #     if round(short_return_amount) == round(invoice_amount):
    #         instance.invoice_group.additional_discount = 0
    #         instance.invoice_group.additional_discount_rate = 0
    #         instance.invoice_group.save(update_fields=['additional_discount', 'additional_discount_rate', ])

    if instance.status in [Status.ACTIVE, Status.INACTIVE, Status.DRAFT]:
        delivery_sheet_invoice_group = DeliverySheetInvoiceGroup.objects.filter(
            invoice_group__id=instance.invoice_group_id).values(
                'pk',
                'delivery_sheet_item',
                'delivery_sheet_item__invoice_group_delivery_sheet',
                'delivery_sheet_item__invoice_group_delivery_sub_sheet',
            )
        if delivery_sheet_invoice_group.exists():
            delivery_sheet_invoice_group = delivery_sheet_invoice_group.last()
            delivery_sheet_invoice_group_id = delivery_sheet_invoice_group['pk']
            delivery_sheet_item_id = delivery_sheet_invoice_group['delivery_sheet_item']
            invoice_group_delivery_sheet_id = delivery_sheet_invoice_group[
                'delivery_sheet_item__invoice_group_delivery_sheet']
            invoice_group_delivery_sub_sheet_id = delivery_sheet_invoice_group[
                'delivery_sheet_item__invoice_group_delivery_sub_sheet']
            update_short_and_return_for_invoice_group_related_models.apply_async(
                (
                    delivery_sheet_invoice_group_id,
                    delivery_sheet_item_id,
                    invoice_group_delivery_sheet_id,
                    invoice_group_delivery_sub_sheet_id,
                    instance.type
                ),
                countdown=5,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )


@transaction.atomic
def post_save_order_invoice_group(sender, instance, created, **kwargs):
    if not created and instance._old_print_count == instance.print_count:
        fields = [
            "additional_discount",
            "additional_discount_rate",
            "additional_cost",
            "additional_cost_rate",
        ]
        order_fields = [
            "amount",
            "round_discount",
            "discount",
        ]
        if (
            instance.additional_discount != instance._old_additional_discount or
            instance.additional_cost != instance._old_additional_cost or
            instance.additional_discount_rate != instance._old_additional_discount_rate or
            instance.additional_cost_rate != instance._old_additional_cost_rate
        ):
            logger.info(f"Applying_additional_discount on OrderInvoiceGroup ID: {instance.id}")
            orders = Purchase.objects.filter(
                invoice_group__id=instance.id
            ).only(
                *fields
            )
            additional_data = instance.to_dict(_fields=fields)

            for order in orders:
                invoice_group_additional_discount_rate = float(additional_data.get("additional_discount_rate", 0))
                order.apply_additional_discount(
                    invoice_group_additional_discount_rate
                )
            # order.__dict__.update(**additional_data)
            # _order_data = order.to_dict(_fields=order_fields)
            # _order_grand_total = _order_data.get("amount", 0) + _order_data.get("round_discount", 0) - _order_data.get("discount", 0)
            # _additional_discount = (float(additional_data.get("additional_discount_rate", 0)) * _order_grand_total) / 100
            # _additional_cost = (float(additional_data.get("additional_cost_rate", 0)) * _order_grand_total) / 100
            # order.additional_discount = _additional_discount
            # order.additional_cost = _additional_cost
            # order.save(update_fields=fields)
            # send_push_notification_for_additional_discount(
            #     order.entry_by_id,
            #     instance.updated_by_id,
            #     _additional_discount,
            #     order.id
            # )
            # order.distributor_order_group.update_order_amount(order=True)
        order_data = Purchase.objects.filter(
            invoice_group__id=instance.id
        ).aggregate(
            sum_amount=Coalesce(Round(Sum(F('amount'))), 0.00),
            sum_discount=Coalesce(Round(Sum(F('discount'))), 0.00),
            sum_round_discount=Coalesce(Round(Sum(F('round_discount'))), 0.00)
        )

        # Update group data
        sender.objects.filter(pk=instance.id).update(
            round_discount=order_data.get('sum_round_discount', 0),
            sub_total=order_data.get('sum_amount', 0),
            discount=order_data.get('sum_discount', 0),
        )
        # Update ES doc
        custom_elastic_rebuild(
            'ecommerce.models.OrderInvoiceGroup',
            {'pk': instance.pk}
        )


def post_save_invoice_group_delivery_sheet(sender, instance, created, **kwargs):
    if instance.status == Status.ACTIVE or instance.status == Status.INACTIVE:
        name = instance.name
        pk = instance.id
        query_params_data = instance.query_params
        if not isinstance(query_params_data, dict):
            json_acceptable_string = query_params_data.replace("'", "\"")
            query_params_data = json.loads(json_acceptable_string)
        delivery_date = query_params_data.get("tentative_delivery_date_1", "")
        delivery_date = datetime.datetime.strptime(delivery_date, "%Y-%m-%d").date().strftime("%d %B, %Y")
        porter = instance.responsible_employee.person.get_full_name_with_code_or_phone()
        if instance.coordinator_id:
            coordinator = instance.coordinator.person.get_full_name_with_code_or_phone()
        else:
            coordinator = "N/A"
        total_data = instance.total_data
        if not isinstance(total_data, dict):
            total_data = total_data.replace("'", "\"")
            total_data = json.loads(total_data)
        total_invoice = total_data.get("total_order_count", 0)
        total_invoice_amount = total_data.get("total_order_amount", 0)
        total_short_amount = total_data.get("total_short_amount", 0)
        total_return_amount = total_data.get("total_return_amount", 0)
        # total_invoice = instance.get_total_invoices_and_amount()['total_invoices']
        # total_invoice_amount = instance.get_total_invoices_and_amount()['total_amount']
        # total_short_amount = instance.get_short_amount()
        # total_return_amount = instance.get_return_amount()
        if created:
            entry_by = instance.generated_by.person.get_full_name_with_code_or_phone()
            created_at = instance.created_at.date().strftime("%d %B, %Y")
            message = f"New delivery Sheet **{name}(#{pk})** created by **{entry_by}** \n" \
                    f"**Created At**: {created_at} \n" \
                    f"**Delivery Date**: {delivery_date} \n" \
                    f"**Porter**: {porter} \n" \
                    f"**Coordinator**: {coordinator} \n" \
                    f"**Total Invoice**: {total_invoice} \n" \
                    f"**Total Invoice Amount**: {total_invoice_amount} \n" \
                    f"**Total Short Amount**: {total_short_amount} \n" \
                    f"**Total Return Amount**: {total_return_amount}"
            send_top_sheet_activity_alert_to_slack_or_mattermost(message=message)
        else:
            if instance.status == Status.INACTIVE:
                if instance.updated_by_id:
                    deleted_by = instance.updated_by.get_full_name_with_code_or_phone()
                else:
                    deleted_by = "N/A"
                deleted_at = instance.updated_at.date().strftime("%d %B, %Y")
                message = f"Delivery Sheet **{name}(#{pk})** deleted by **{deleted_by}** \n" \
                        f"**Deleted At**: {deleted_at} \n" \
                        f"**Delivery Date**: {delivery_date} \n" \
                        f"**Porter**: {porter} \n" \
                        f"**Coordinator**: {coordinator} \n" \
                        f"**Total Invoice**: {total_invoice} \n" \
                        f"**Total Invoice Amount**: {total_invoice_amount} \n" \
                        f"**Total Short Amount**: {total_short_amount} \n" \
                        f"**Total Return Amount**: {total_return_amount}"
                send_top_sheet_activity_alert_to_slack_or_mattermost(message=message)


def store_old_instance_value(sender, instance, **kwargs):
    """This function stores order invoice group in model attribute and pass it to post save"""
    old_print_count = 0
    if not instance._state.adding:
        try:
            old_instance = sender.objects.only(
                "print_count",
                "additional_cost",
                "additional_discount",
                "additional_discount_rate",
                "additional_cost_rate",
            ).get(pk=instance.pk)
            old_print_count = old_instance.print_count
            old_additional_cost = old_instance.additional_cost
            old_additional_discount = old_instance.additional_discount
            old_additional_discount_rate = old_instance.additional_discount_rate
            old_additional_cost_rate = old_instance.additional_cost_rate
        except sender.DoesNotExist:
            old_instance.print_count = 0

    try:
        instance._old_print_count = old_print_count
        instance._old_additional_discount = old_additional_discount
        instance._old_additional_cost = old_additional_cost
        instance._old_additional_discount_rate = old_additional_discount_rate
        instance._old_additional_cost_rate = old_additional_cost_rate
    except Exception as e: #handling universally as quick fix TODO: use exception for only this case
        logger.info(
            f"Ignoring additional as instance is in create state: instance._state.adding {instance._state.adding}"
        )
