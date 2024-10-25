import logging
import os
from django.db import transaction
from common.enums import Status
from common.helpers import (
    get_request_object,
)
from common.user_agents_helpers import get_user_device_info_from_request
from common.cache_helpers import delete_qs_count_cache
from pharmacy.helpers import get_product_short_name

from .enums import ProcureItemType, ProcureIssueType, PredictionItemMarkType, RateStatus
from .helpers import send_procure_alert_to_slack

logger = logging.getLogger(__name__)


@transaction.atomic
def post_save_procure_item(sender, instance, created, **kwargs):
    from .tasks import update_purchase_order_qty_for_pred_item

    if created:
        if instance.type == ProcureItemType.IN and instance.prediction_item_id and instance.status == Status.ACTIVE:
            instance.prediction_item.purchase_order += instance.quantity
            instance.prediction_item.save(update_fields=['purchase_order',])
            product_full_name = get_product_short_name(instance.stock.product)
            if instance.rate_status == RateStatus.HIGHER_THAN_RANGE:
                message = f"`{product_full_name}` Procured by `{instance.procure.employee.get_full_name()}` from `{instance.procure.supplier.company_name} with  *`Higher Rate`*"
                send_procure_alert_to_slack(message)
        update_purchase_order_qty_for_pred_item.apply_async(
            (instance.prediction_item_id, ),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
    # Delete qs count cache
    delete_qs_count_cache(sender)


@transaction.atomic
def pre_save_procure_item(sender, instance, **kwargs):
    from .tasks import update_purchase_order_qty_for_pred_item

    if not instance._state.adding:
        old_instance = sender.objects.get(pk=instance.pk)
        # Delete procure item instance
        if old_instance.status == Status.ACTIVE and instance.status == Status.INACTIVE and instance.prediction_item_id:
            instance.prediction_item.purchase_order -= instance.quantity
            instance.prediction_item.save(update_fields=['purchase_order',])
            update_purchase_order_qty_for_pred_item.apply_async(
                    (instance.prediction_item_id, ),
                    countdown=5,
                    retry=True, retry_policy={
                        'max_retries': 10,
                        'interval_start': 0,
                        'interval_step': 0.2,
                        'interval_max': 0.2,
                    }
                )


@transaction.atomic
def pre_save_procure_group(sender, instance, **kwargs):
    from .models import Procure

    if not instance._state.adding:
        old_instance = sender.objects.get(pk=instance.pk)
        # Delete procure group instance
        if old_instance.status == Status.ACTIVE and instance.status == Status.INACTIVE:
            procures = instance.procure_group_procures.filter(status=Status.ACTIVE)
            for item in procures:
                item.status = Status.INACTIVE
                item.save(update_fields=['status',])
        # Update requisition id for related procures (While cloning requisition)
        if old_instance.requisition_id != instance.requisition_id:
            procures = Procure.objects.filter(
                status=Status.ACTIVE,
                procure_group__id=instance.id
            )
            procures.update(requisition_id=instance.requisition_id)
    # Delete qs count cache
    delete_qs_count_cache(sender)

@transaction.atomic
def pre_save_procure(sender, instance, **kwargs):
    if not instance._state.adding:
        old_instance = sender.objects.get(pk=instance.pk)
        # Delete procure instance
        if old_instance.status == Status.ACTIVE and instance.status == Status.INACTIVE:
            procure_items = instance.procure_items.filter(status=Status.ACTIVE)
            for item in procure_items:
                item.status = Status.INACTIVE
                item.save(update_fields=['status',])
            is_edit = sender.objects.filter(status=Status.ACTIVE, copied_from__id=instance.pk).exists()
            if not is_edit:
                try:
                    request = get_request_object()
                    request_user_context = get_user_device_info_from_request(request)
                    device_info = (
                        f'**User IP:** {request_user_context.get("ip", "")}\n'
                        f'**Device Type:** {request_user_context.get("device_type", "")}\n'
                        f'**Browser Type:** {request_user_context.get("browser_type", "")}({request_user_context.get("browser_version", "")})\n'
                        f'**OS Type:** {request_user_context.get("os_type", "")}({request_user_context.get("os_version", "")})\n'
                    )
                    message = f"Deleted Procurement Purchase(#{instance.id}) from `{instance.supplier.company_name}` of amount BDT `{instance.sub_total}` by `{request.user.get_full_name()}` of Buyer `{instance.employee.get_full_name()}`.\n{device_info}"
                    send_procure_alert_to_slack(message)
                except AttributeError:
                    logger.info("Ignoring sending message to slack as device info missing!")

@transaction.atomic
def post_save_procure(sender, instance, created, **kwargs):
    from procurement.models import ProcureReturn, ProcurePayment, Procure
    if created:
        try:
            request = get_request_object()
            request_user_context = get_user_device_info_from_request(request)
            device_info = (
                f'**User IP:** {request_user_context.get("ip", "")}\n'
                f'**Device Type:** {request_user_context.get("device_type", "")}\n'
                f'**Browser Type:** {request_user_context.get("browser_type", "")}({request_user_context.get("browser_version", "")})\n'
                f'**OS Type:** {request_user_context.get("os_type", "")}({request_user_context.get("os_version", "")})\n'
            )
        except AttributeError:
            device_info = (
                f'**User IP:** \n'
                f'**Device Type:** \n'
                f'**Browser Type:** '
                f'**OS Type:** \n'
            )
            logger.info("Ignoring device as info missing!")
        if instance.copied_from_id:
            message = f"Edited Procurement Purchase(#{instance.copied_from_id}) as (#{instance.id}) from `{instance.supplier.company_name}` of amount BDT `{instance.sub_total}` by `{request.user.get_full_name()}` of Buyer `{instance.employee.get_full_name()}`.\n{device_info}"
            # Update the new procure_id to the existing procure returns
            ProcureReturn().get_all_actives().filter(
                procure_id=instance.copied_from_id
                ).update(procure_id=instance.id)
            # Update the new procure id to the existing procure payments
            ProcurePayment().get_all_actives().filter(
                procure_id=instance.copied_from_id
            ).update(procure_id=instance.id)
            Procure.objects.get(id=instance.copied_from_id).history.all().update(id=instance.id)

            # retrieve previous procure to compere
            procure = Procure.objects.get(id=instance.copied_from_id)
            if procure.procure_group_id:
                instance.procure_group_id = procure.procure_group_id
                instance.current_status = procure.current_status
                # set the old procure date to the new instance
                instance.date = procure.date
            if procure.requisition_id:
                instance.requisition_id = procure.requisition_id

            instance.save()
            logger.info(f"Moved history of procure from procure id: {instance.copied_from_id} to {instance}")
        else:
            message = f"New Procurement Purchase(#{instance.id}) from `{instance.supplier.company_name}` of amount BDT `{instance.sub_total}` by `{instance.employee.get_full_name()}`.\n{device_info}"
        send_procure_alert_to_slack(message)
    # Delete qs count cache
    delete_qs_count_cache(sender)

@transaction.atomic
def post_save_procure_issue_log(sender, instance, created, **kwargs):
    if created:
        product_full_name = get_product_short_name(instance.stock.product)
        issue_types = dict(ProcureIssueType().choicify())
        message = f"`{product_full_name}` Marked as Procure Issue by `{instance.employee.get_full_name()}`, Reason: `{issue_types.get(instance.type)}`"
        send_procure_alert_to_slack(message)
    # Delete qs count cache
    delete_qs_count_cache(sender)

@transaction.atomic
def post_save_prediction_item_mark(sender, instance, created, **kwargs):
    if created:
        instance.prediction_item.marked_status = instance.type
        instance.prediction_item.save(update_fields=['marked_status',])
        product_full_name = get_product_short_name(instance.prediction_item.stock.product)
        if instance.type == PredictionItemMarkType.MARK:
            message = f"`{product_full_name}` Marked by `{instance.employee.get_full_name()}` from `{instance.supplier.company_name}`"
            if instance.rate:
                message += f" Rate: `{instance.rate}`"
        else:
            message = f"`{product_full_name}` Unmarked by `{instance.employee.get_full_name()}` from `{instance.supplier.company_name}"
        send_procure_alert_to_slack(message)

@transaction.atomic
def post_save_procure_status(sender, instance, created, **kwargs):
    if created:
        instance.procure.current_status = instance.current_status
        instance.procure.save(update_fields=['current_status',])

