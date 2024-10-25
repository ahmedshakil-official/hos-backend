from django.core.management.base import BaseCommand
from django.db.models import Sum, Q, F, Case, When, Count
from django.db.models.functions import Coalesce

from common.enums import Status
from ecommerce.models import (
    DeliverySheetInvoiceGroup,
    InvoiceGroupDeliverySheet, DeliverySheetItem
)
import logging, decimal
from tqdm import tqdm

from ecommerce.enums import ShortReturnLogType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info("Populate Shorts and Returns For DeliverySheetInvoiceGroup, InvoiceGroupDeliverySheet, "
                    "DeliverySheetItem models and save to DB")

        invoice_group_delivery_sheet = InvoiceGroupDeliverySheet.objects.all().values(
            'id',
            'short_amount', 'return_amount', 'total_data'
        ).annotate(
            total_short_invoice_group_delivery_sheet=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_short_invoice_group_delivery_sheet_draft=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_return_invoice_group_delivery_sheet=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_return_invoice_group_delivery_sheet_draft=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT),
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0))
        )
        invoice_group_delivery_sheet_obj_to_be_updated = []
        for data in tqdm(invoice_group_delivery_sheet):
            invoice_group_delivery_sheet_total_data = {
                'total_order_amount': data['total_data']['total_order_amount'],
                'total_short_amount': data['total_short_invoice_group_delivery_sheet'],
                'total_short_amount_draft': data['total_short_invoice_group_delivery_sheet_draft'],
                'total_return_amount': data['total_return_invoice_group_delivery_sheet'],
                'total_return_amount_draft': data['total_return_invoice_group_delivery_sheet_draft'],
                'total_unique_item': data['total_data']['total_unique_item'],
                'total_item': data['total_data']['total_item'],
                'total_order_count': data['total_data']['total_order_count']
            }
            invoice_group_delivery_sheet_obj_to_be_updated.append(
                InvoiceGroupDeliverySheet(
                    id=data['id'],
                    short_amount=data['total_short_invoice_group_delivery_sheet'],
                    return_amount=data['total_return_invoice_group_delivery_sheet'],
                    total_data=invoice_group_delivery_sheet_total_data
                )
            )
        InvoiceGroupDeliverySheet.objects.bulk_update(
            objs=invoice_group_delivery_sheet_obj_to_be_updated,
            fields=['short_amount', 'return_amount', 'total_data'],
            batch_size=100,
        )
        logger.info("Successfully updated InvoiceGroupDeliverySheet")
        delivery_sheet_invoice_group = DeliverySheetInvoiceGroup.objects.all().values(
            'id',
            'total_short', 'total_return'
        ).annotate(
            total_short_delivery_sheet_invoice_group=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F(
                    'invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_return_delivery_sheet_invoice_group=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F(
                    'invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
        )
        delivery_sheet_invoice_group_obj_to_be_updated = []
        for data in tqdm(delivery_sheet_invoice_group):
            delivery_sheet_invoice_group_obj_to_be_updated.append(
                DeliverySheetInvoiceGroup(
                    id=data['id'],
                    total_short=data['total_short_delivery_sheet_invoice_group'],
                    total_return=data['total_return_delivery_sheet_invoice_group'],
                )
            )
        DeliverySheetInvoiceGroup.objects.bulk_update(
            objs=delivery_sheet_invoice_group_obj_to_be_updated,
            fields=['total_short', 'total_return'],
            batch_size=100,
        )
        logger.info("Successfully updated DeliverySheetInvoiceGroup")

        delivery_sheet_item = DeliverySheetItem.objects.all().values(
            'id', 'organization_id',
            'total_item_short', 'total_item_return',
        ).annotate(
            total_short_delivery_sheet_item=Coalesce(Sum(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__organization_id=F(
                    'organization_id')),
                then='delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__quantity'
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_return_delivery_sheet_item=Coalesce(Sum(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__organization_id=F(
                    'organization_id')),
                then='delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__quantity'
            ), default=decimal.Decimal(0))), decimal.Decimal(0)),
            total_short_unique_delivery_sheet_item=Count(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__stock__id'))),
                distinct=True),
            total_return_unique_delivery_sheet_item=Count(Case(When(
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_items__stock__id'))),
                distinct=True),
        )
        delivery_sheet_item_obj_to_be_updated = []
        for data in tqdm(delivery_sheet_item):
            delivery_sheet_item_obj_to_be_updated.append(
                DeliverySheetItem(
                    id=data['id'],
                    total_item_short=data['total_short_delivery_sheet_item'],
                    total_item_return=data['total_return_delivery_sheet_item'],
                    total_unique_item_short=data['total_short_unique_delivery_sheet_item'],
                    total_unique_item_return=data['total_return_unique_delivery_sheet_item'],
                )
            )
        DeliverySheetItem.objects.bulk_update(
            objs=delivery_sheet_item_obj_to_be_updated,
            fields=['total_item_short', 'total_item_return', 'total_unique_item_short', 'total_unique_item_return'],
            batch_size=100,
        )
        logger.info("Successfully updated DeliverySheetItem")
        logger.info("Successfully DONE!!!")
