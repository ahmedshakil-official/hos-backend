import datetime, decimal
import pandas as pd

from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from tabulate import tabulate

from django.db import models
from django.utils.translation import gettext as _
from django.db.models.signals import post_save, pre_save
from django.db.models import Sum, Case, When, F, FloatField, Count, IntegerField, DecimalField, Q
from django.db.models.functions import Coalesce, Cast
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg

from enumerify import fields

from common.models import (
    CreatedAtUpdatedAtBaseModelWithOrganization,
    CreatedAtUpdatedAtBaseModel,
    FileStorage,
)
from common.fields import JSONTextField
from common.helpers import custom_elastic_rebuild
from common.utils import (
    DistinctSum,
    ArrayLength
)
from common.enums import Status
from pharmacy.enums import OrderTrackingStatus
from expo_notification.tasks import send_push_notification_to_mobile_app_by_org
from pharmacy.models import Stock
from .enums import ShortReturnLogType, FailedDeliveryReason
from .signals import (
    pre_save_short_return_item,
    post_save_order_invoice_group,
    pre_save_short_return_log,
    post_save_invoice_group_delivery_sheet,
    post_save_short_return_log,
    store_old_instance_value,
)

from .enums import TopSheetType

class ShortReturnLog(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    # Who entry the short/return
    received_by = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        verbose_name=('Person Organization entry a short or return'),
        related_name='short_return_received_by'
    )
    # Who approve the return
    approved_by = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=('Person Organization approve a short or return'),
        related_name='short_return_approved_by'
    )
    order_by_organization = models.ForeignKey(
        'core.Organization', models.DO_NOTHING,
        related_name='short_return_organization_order_by'
    )
    order = models.ForeignKey(
        'pharmacy.Purchase', models.DO_NOTHING,
        related_name='short_return_orders'
    )
    invoice_group = models.ForeignKey(
        'ecommerce.OrderInvoiceGroup',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='invoice_groups',
        help_text='Order invoice group for distributor order'
    )
    order_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    short_return_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_order_items = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_order_unique_items = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_short_return_items = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_short_return_unique_items = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    type = fields.SelectIntegerField(
        blueprint=ShortReturnLogType,
        default=ShortReturnLogType.SHORT
    )
    round_discount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    remarks = models.TextField(
        blank=True,
        null=True
    )
    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.order, self.received_by)

    def change_short_return_items_status(self, previous_status, current_status):
        short_return_items = self.short_return_items.filter(
                status=previous_status
            ).only('id', 'status')
        for short_return_item in short_return_items:
            short_return_item.status = current_status
            short_return_item.updated_by_id = self.updated_by_id
            short_return_item.save(update_fields=['status', 'updated_by_id', ])

    def validate_delete(self):
        days_allowed = 3
        if self.invoice_group.delivery_date < timezone.now().date() - datetime.timedelta(days=days_allowed):
            raise ValidationError(
                {
                    "detail": f"Cannot delete short return log for invoice group older than {days_allowed} days"
                },
            )
        return True


class ShortReturnItem(CreatedAtUpdatedAtBaseModelWithOrganization):
    type = fields.SelectIntegerField(
        blueprint=ShortReturnLogType,
        default=ShortReturnLogType.SHORT
    )
    stock = models.ForeignKey(
        'pharmacy.Stock',
        models.DO_NOTHING,
        related_name='stocks_short_return'
    )
    stock_io = models.ForeignKey(
        'pharmacy.StockIOLog',
        models.DO_NOTHING,
        related_name='stock_io_short_return'
    )
    short_return_log = models.ForeignKey(
        ShortReturnLog, models.DO_NOTHING,
        related_name='short_return_items'
    )
    product_name = models.CharField(max_length=512)
    order_quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    batch = models.CharField(max_length=128)
    expire_date = models.DateField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    discount_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discount_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    vat_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    vat_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    tax_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    tax_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    unit_name = models.CharField(max_length=56)
    round_discount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.created_at, self.stock)


class OrderInvoiceGroup(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    delivery_date = models.DateField(blank=True, null=True)
    sub_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    round_discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    additional_discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    additional_discount_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    additional_cost = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    additional_cost_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    order_by_organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        related_name='invoice_groups',
        help_text='Organization order by'
    )
    current_order_status = fields.SelectIntegerField(
        blueprint=OrderTrackingStatus,
        default=OrderTrackingStatus.PENDING,
        help_text='Define current status of order'
    )
    failed_delivery_reason = fields.SelectIntegerField(
        blueprint=FailedDeliveryReason,
        default=FailedDeliveryReason.DEFAULT,
        help_text='Define reason for a failed delivery'
    )
    responsible_employee = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='invoice_groups',
        blank=True,
        null=True,
        verbose_name=('responsible person organization for order group'),
    )
    print_count = models.PositiveIntegerField(default=0)
    total_short = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_return = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    copied_from = models.ForeignKey(
        'self', models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
    )

    secondary_responsible_employee = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='secondary_invoice_groups',
        blank=True,
        null=True,
        verbose_name='secondary responsible person organization for order group',
    )
    customer_rating = models.PositiveIntegerField(
        default=0,
        validators=[
            MaxValueValidator(5),
            MinValueValidator(0)
        ]
    )
    customer_comment = models.TextField(
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When Porter delivered the order'
    )
    additional_dynamic_discount_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="Additional discount amount customer get due to dynamic discount"
    )
    additional_dynamic_discount_percentage = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="Additional discount percentage customer get due to dynamic discount"
    )

    class Meta:
        verbose_name = "Order Invoice Group"
        verbose_name_plural = "Order Invoice Groups"
        ordering = ('-pk',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.organization_id)

    def related_invoice_groups(self, pk_list = False):
        invoices = OrderInvoiceGroup.objects.filter(
            order_by_organization__id=self.order_by_organization_id,
            delivery_date=self.delivery_date,
        ).exclude(
            pk=self.pk
        )
        if pk_list:
            return invoices.values_list('pk', flat=True)
        return invoices

    def send_push_notification_on_short(self, entry_by_id=None):
        short_return_log_orders = list(self.invoice_groups.filter(
            type=ShortReturnLogType.SHORT
        ).values_list('order_id', flat=True))

        short_return_items = list(ShortReturnItem.objects.filter(
            short_return_log__invoice_group__id=self.id,
            type=ShortReturnLogType.SHORT
        ).order_by().values(
            'stock_id',
            'product_name',
        ).annotate(
            short_qty=Sum('quantity', output_field=FloatField())
        ))
        # Prepare data for tabular view
        short_return_items_tabular_data = []
        for index, item in enumerate(short_return_items):
            short_return_items_tabular_data.append(
            [index + 1, item.get('product_name', ''),  item.get('short_qty', '')]
        )

        tabulate_data = tabulate(short_return_items_tabular_data, headers=['Sl','Name','Short Qty.'], disable_numparse=True)
        title = "Order Marked as short"
        order_text = f'{self.id}({", ".join(map(str, short_return_log_orders))})'
        body = f"We are sorry, following items of the order #{order_text} marked as short\n\n{tabulate_data}\n\nTotal short amount {round(self.short_total, 2)}"
        # Send push notification
        if short_return_items:
            send_push_notification_to_mobile_app_by_org.delay(
                org_ids=[self.order_by_organization_id],
                title=title,
                body=body,
                data={},
                entry_by_id=entry_by_id
            )

    def get_total_short_return_data(self):
        data = self.invoice_groups.filter(
            status=Status.ACTIVE,
        ).only('short_return_amount').aggregate(
            total_short=Coalesce(Sum(Case(When(
                type=ShortReturnLogType.SHORT,
                status=Status.ACTIVE,
                then=F('short_return_amount') + F('round_discount')),
                output_field=DecimalField())), decimal.Decimal(0)),
            total_return=Coalesce(Sum(Case(When(
                type=ShortReturnLogType.RETURN,
                status=Status.ACTIVE,
                then=F('short_return_amount') + F('round_discount')),
                output_field=DecimalField(),)), decimal.Decimal(0)),
        )
        return data

    @property
    def short_total(self):
        shorts = self.invoice_groups.filter(
            status=Status.ACTIVE,
            type=ShortReturnLogType.SHORT
        ).aggregate(
            total_amount=Coalesce(
                Sum(F('short_return_amount') + F('round_discount')), decimal.Decimal(0)
            )
        )
        return shorts.get('total_amount', 0)

    @property
    def return_total(self):
        returns = self.invoice_groups.filter(
            status=Status.ACTIVE,
            type=ShortReturnLogType.RETURN
        ).aggregate(
            total_amount=Coalesce(
                Sum(F('short_return_amount') + F('round_discount')), decimal.Decimal(0)
            )
        )
        return returns.get('total_amount', 0)

    @property
    def info(self):
        queryset = self.__class__.objects.annotate(
            unique_item=Count(Case(When(
                orders__stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                then=F('orders__stock_io_logs__stock'))), distinct=True),
            total_item=Coalesce(Sum(Case(When(
                orders__stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                then=F('orders__stock_io_logs__quantity')))), 0.00),
            order_invoice_group_ids=ArrayAgg(Cast('pk', IntegerField()), distinct=True),
            order_invoice_group_count=ArrayLength('order_invoice_group_ids'),
        ).get(pk=self.id)
        short_return_instances = ShortReturnItem.objects.filter(
            short_return_log__order__invoice_group__pk=self.id
        ).only(
            'stock_id',
            'quantity',
            'short_return_log__id'
        )
        data = short_return_instances.aggregate(
            unique_short_quantity=Count(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.SHORT,
                then=F('stock_id')),
                output_field=IntegerField()), distinct=True),
            unique_short_draft_quantity=Count(Case(When(
                status=Status.DRAFT,
                type=ShortReturnLogType.SHORT,
                then=F('stock_id')),
                output_field=IntegerField()), distinct=True),
            unique_return_quantity=Count(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.RETURN,
                then=F('stock_id')),
                output_field=IntegerField()), distinct=True),
            unique_return_draft_quantity=Count(Case(When(
                status=Status.DRAFT,
                type=ShortReturnLogType.RETURN,
                then=F('stock_id')),
                output_field=IntegerField()), distinct=True),
            total_short_quantity=Coalesce(Sum(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.SHORT,
                then=F('quantity')),
                output_field=IntegerField())), 0),
            total_short_quantity_draft=Coalesce(Sum(Case(When(
                status=Status.DRAFT,
                type=ShortReturnLogType.SHORT,
                then=F('quantity')),
                output_field=IntegerField())), 0),
            total_return_quantity=Coalesce(Sum(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.RETURN,
                then=F('quantity')),
                output_field=IntegerField())), 0),
            total_return_quantity_draft=Coalesce(Sum(Case(When(
                status=Status.DRAFT,
                type=ShortReturnLogType.RETURN,
                then=F('quantity')),
                output_field=IntegerField())), 0),
        )

        total_short_draft_amount = short_return_instances.filter(
            status=Status.DRAFT,
            type=ShortReturnLogType.SHORT
        ).aggregate(
            total_amount=Coalesce(
                DistinctSum(
                    F('short_return_log__short_return_amount') + F('short_return_log__round_discount')
                ), decimal.Decimal(0)
        )).get('total_amount', 0)

        total_return_draft_amount = short_return_instances.filter(
            status=Status.DRAFT,
            type=ShortReturnLogType.RETURN
        ).aggregate(
            total_amount=Coalesce(
                DistinctSum(
                    F('short_return_log__short_return_amount') + F('short_return_log__round_discount')
                ), decimal.Decimal(0)
        )).get('total_amount', 0)

        data['total_short_draft_amount'] = total_short_draft_amount
        data['total_return_draft_amount'] = total_return_draft_amount
        data['unique_item'] = queryset.unique_item
        data['total_item'] = queryset.total_item
        data['order_invoice_group_count'] = queryset.order_invoice_group_count
        return data

    def is_valid_for_clone(self):
        invoice_groups = OrderInvoiceGroup.objects.filter(
            copied_from__id=self.id
        ).only('id',)
        return not invoice_groups.exists(), invoice_groups.first()


    def clone_invoice_group(self, delivery_date, request_user_id):
        import time
        from datetime import datetime
        from dateutil import parser
        from expo_notification.tasks import send_push_notification_to_mobile_app
        from pharmacy.enums import OrderTrackingStatus

        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
        _datetime_now = datetime.strptime(
            time.strftime(DATE_TIME_FORMAT, time.localtime()),
            DATE_TIME_FORMAT
        )
        _delivery_date = parser.parse(delivery_date).date()

        ignore_fields = [
            'id',
            'status',
            'entry_by',
            'updated_by',
            'responsible_employee',
            'secondary_responsible_employee',
            'print_count',
            'total_short',
            'total_return',
            'date',
            'current_order_status',
            'delivery_date',
            'copied_from',
        ]

        fk_fields = [
            'organization',
            'order_by_organization',
        ]

        invoice_group_data = self.to_dict(_exclude=ignore_fields)
        for item in fk_fields:
            invoice_group_data[f'{item}_id'] = invoice_group_data.pop(item)

        invoice_group_data['date'] = _datetime_now
        invoice_group_data['copied_from_id'] = self.id
        invoice_group_data['delivery_date'] = _delivery_date
        invoice_group_data['current_order_status'] = OrderTrackingStatus.ACCEPTED
        invoice_group_data['entry_by_id'] = request_user_id

        new_order_invoice_group = OrderInvoiceGroup.objects.create(**invoice_group_data)
        new_order_invoice_group_id = new_order_invoice_group.id
        custom_elastic_rebuild(
            'ecommerce.models.OrderInvoiceGroup', {'pk': new_order_invoice_group_id}
        )

        orders = self.orders.filter()

        for order in orders:
            new_order, order_group = order.clone_order(new_order_invoice_group_id, _delivery_date)
            notification_title = "Order Update"
            notification_body = f"We are sorry for the failed delivery of #{order.id} instead we will deliver #{new_order.id}"
            notification_data = {
                "order_alias": str(new_order.alias),
                "order_group_alias": str(order_group.alias)
            }
            send_push_notification_to_mobile_app.delay(
                new_order.entry_by_id,
                title=notification_title,
                body=notification_body,
                data=notification_data,
                entry_by_id=request_user_id
            )
        custom_elastic_rebuild(
            'pharmacy.models.Purchase', {'invoice_group__id': new_order_invoice_group_id}
        )

        return self.id, new_order_invoice_group_id

class InvoiceGroupPdf(FileStorage):
    invoice_group = models.ForeignKey(
        OrderInvoiceGroup,
        models.DO_NOTHING,
        db_index=True,
        related_name="invoice_pdfs",
        verbose_name=("invoice group")
    )

    def __str__(self):
        return self.get_name()
from core.models import Area

class InvoicePdfGroup(FileStorage):
    delivery_date = models.DateField()
    invoice_groups = models.JSONField(
        default=list,
    )
    download_count = models.PositiveSmallIntegerField(default=0)
    invoice_count = models.PositiveIntegerField(default=0)
    page_count = models.PositiveIntegerField(default=0)
    repeat = models.PositiveSmallIntegerField()
    area = models.ForeignKey(
        Area,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name = "area_pdf_groups"
    )

    def __str__(self):
        return self.get_name()


class InvoiceGroupDeliverySheet(CreatedAtUpdatedAtBaseModelWithOrganization):
    name = models.CharField(max_length=256)
    date = models.DateTimeField()
    query_params = JSONTextField(blank=True, null=True, default='{}')
    filter_data = JSONTextField(blank=True, null=True, default='{}')
    total_data = JSONTextField(blank=True, null=True, default='{}')
    responsible_employee = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='invoice_group_delivery_sheets',
        blank=True,
        null=True,
        help_text='Filter responsible employee(delivery guy)'
    )
    coordinator = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='coordinator_invoice_group_delivery_sheets',
        blank=True,
        null=True,
        help_text='Coordinator of the delivery guy'
    )
    generated_by = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='generated_by_invoice_group_delivery_sheets',
        blank=True,
        null=True,
        help_text='User generate the report'
    )
    order_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    short_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    return_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)

    type = models.CharField(
        max_length=50,
        choices=TopSheetType.choices,
        default=TopSheetType.DEFAULT,
    )

    class Meta:
        verbose_name = "Invoice Group Delivery Sheet"
        verbose_name_plural = "Invoice Group Delivery Sheets"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.name)

    def get_sub_top_sheet_short_return_data(self):
        sub_top_sheet_pk_list = TopSheetSubTopSheet().get_all_actives().filter(
            top_sheet=self.id
        ).values_list(
            "sub_top_sheet_id",
            flat=True
        )
        invoices = DeliverySheetInvoiceGroup.objects.filter(
            delivery_sheet_item__invoice_group_delivery_sub_sheet__id__in=list(sub_top_sheet_pk_list)
        )
        partial_return_filters = {
            "invoice_group__invoice_groups__status": Status.ACTIVE,
            "invoice_group__invoice_groups__type": ShortReturnLogType.RETURN,
            "invoice_group__current_order_status__in":[OrderTrackingStatus.PARITAL_DELIVERED, OrderTrackingStatus.PORTER_PARTIAL_DELIVERED]
        }
        full_return_filters = {
            "invoice_group__invoice_groups__status": Status.ACTIVE,
            "invoice_group__invoice_groups__type": ShortReturnLogType.RETURN,
            "invoice_group__current_order_status__in": [OrderTrackingStatus.FULL_RETURNED, OrderTrackingStatus.PORTER_FULL_RETURN]
        }
        short_filters = {
            "invoice_group__invoice_groups__status": Status.ACTIVE,
            "invoice_group__invoice_groups__type" :ShortReturnLogType.SHORT
        }
        data = invoices.values(
            "delivery_sheet_item__invoice_group_delivery_sub_sheet__id"
        ).annotate(
            partial_return_total=Coalesce(Sum(
                F("invoice_group__invoice_groups__short_return_amount") + F("invoice_group__invoice_groups__round_discount"),
                filter=Q(**partial_return_filters)
            ), decimal.Decimal(0)),
            partial_return_unique_pharmacy=Count("invoice_group__order_by_organization", distinct=True, filter=Q(**partial_return_filters)),
            full_return_total=Coalesce(Sum(
                F("invoice_group__invoice_groups__short_return_amount") + F("invoice_group__invoice_groups__round_discount"),
                filter=Q(**full_return_filters)
            ), decimal.Decimal(0)),
            full_return_unique_pharmacy=Count("invoice_group__order_by_organization", distinct=True, filter=Q(**full_return_filters)),
            short_total=Coalesce(Sum(
                F("invoice_group__invoice_groups__short_return_amount") + F("invoice_group__invoice_groups__round_discount"),
                filter=Q(**short_filters)
            ), decimal.Decimal(0))
        )
        data_df = pd.DataFrame(list(data))
        if not data_df.empty:
            data_df = data_df.rename(
                columns={
                    "delivery_sheet_item__invoice_group_delivery_sub_sheet__id": "invoice_group_delivery_sub_sheet_id",
                }
            )
            return data_df.to_dict("records")
        return []

    def approve_short_return_by_delivery_sheet(self, approved_by_id, updated_by_id = None):
        update_fields = ['status', 'approved_by_id']
        # Find invoices by delivery sheet
        invoices = DeliverySheetInvoiceGroup.objects.filter(
            delivery_sheet_item__invoice_group_delivery_sheet__id=self.id
        ).values_list('invoice_group_id', flat=True)

        # Find short return logs of related invoices
        short_return_logs = ShortReturnLog.objects.filter(
            status=Status.DRAFT,
            invoice_group_id__in=invoices
        )

        # Update status to active
        for short_return_log in short_return_logs:
            short_return_log.status = Status.ACTIVE
            short_return_log.approved_by_id = approved_by_id
            if updated_by_id:
                short_return_log.updated_by_id = updated_by_id
                short_return_log.approved_at = datetime.datetime.now()
                update_fields += ['updated_by_id', 'approved_at']
            short_return_log.save(update_fields=update_fields)

        # get return amount for this invoices
        # partial_return_amount = invoices.filter(
        #     invoice_group__invoice_groups__status=Status.ACTIVE,
        #     invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
        #     invoice_group__current_order_status__in=[OrderTrackingStatus.PARITAL_DELIVERED, OrderTrackingStatus.PORTER_PARTIAL_DELIVERED]).aggregate(
        #     return_total=Coalesce(Sum(
        #         F('invoice_group__invoice_groups__short_return_amount') + F('invoice_group__invoice_groups__round_discount')
        #     ), decimal.Decimal(0)),
        #     unique_pharmacy=Count('invoice_group__order_by_organization', distinct=True)
        # )

        # full_return_amount = invoices.filter(
        #     invoice_group__invoice_groups__status=Status.ACTIVE,
        #     invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
        #     invoice_group__current_order_status__in=[OrderTrackingStatus.FULL_RETURNED, OrderTrackingStatus.PORTER_FULL_RETURN]).aggregate(
        #     return_total=Coalesce(Sum(
        #         F('invoice_group__invoice_groups__short_return_amount') + F('invoice_group__invoice_groups__round_discount')
        #     ), decimal.Decimal(0)),
        #     unique_pharmacy=Count('invoice_group__order_by_organization', distinct=True)
        # )

        # total_short = invoices.filter(
        #     invoice_group__invoice_groups__status=Status.ACTIVE,
        #     invoice_group__invoice_groups__type=ShortReturnLogType.SHORT).aggregate(
        #     return_total=Coalesce(Sum(
        #         F('invoice_group__invoice_groups__short_return_amount') + F('invoice_group__invoice_groups__round_discount')
        #     ), decimal.Decimal(0)))
        # # Return True if any draft short_return exists otherwise False
        # context = {
        #     'total_short': total_short['return_total'],
        #     'full_return_amount': full_return_amount['return_total'],
        #     'full_return_unique_pharmacy': full_return_amount['unique_pharmacy'],
        #     'partial_return_amount': partial_return_amount['return_total'],
        #     'partial_return_unique_pharmacy': partial_return_amount['unique_pharmacy'],
        #     'sub_top_sheet_items': self.get_sub_top_sheet_short_return_data()
        # }
        partial_return_filters = {
            "invoice_group__invoice_groups__status": Status.ACTIVE,
            "invoice_group__invoice_groups__type": ShortReturnLogType.RETURN,
            "invoice_group__current_order_status__in":[OrderTrackingStatus.PARITAL_DELIVERED, OrderTrackingStatus.PORTER_PARTIAL_DELIVERED]
        }
        full_return_filters = {
            "invoice_group__invoice_groups__status": Status.ACTIVE,
            "invoice_group__invoice_groups__type": ShortReturnLogType.RETURN,
            "invoice_group__current_order_status__in": [OrderTrackingStatus.FULL_RETURNED, OrderTrackingStatus.PORTER_FULL_RETURN]
        }
        short_filters = {
            "invoice_group__invoice_groups__status": Status.ACTIVE,
            "invoice_group__invoice_groups__type" :ShortReturnLogType.SHORT
        }
        data = invoices.aggregate(
            partial_return_total=Coalesce(Sum(
                F("invoice_group__invoice_groups__short_return_amount") + F("invoice_group__invoice_groups__round_discount"),
                filter=Q(**partial_return_filters)
            ), decimal.Decimal(0)),
            partial_return_unique_pharmacy=Count("invoice_group__order_by_organization", distinct=True, filter=Q(**partial_return_filters)),
            full_return_total=Coalesce(Sum(
                F("invoice_group__invoice_groups__short_return_amount") + F("invoice_group__invoice_groups__round_discount"),
                filter=Q(**full_return_filters)
            ), decimal.Decimal(0)),
            full_return_unique_pharmacy=Count("invoice_group__order_by_organization", distinct=True, filter=Q(**full_return_filters)),
            short_total=Coalesce(Sum(
                F("invoice_group__invoice_groups__short_return_amount") + F("invoice_group__invoice_groups__round_discount"),
                filter=Q(**short_filters)
            ), decimal.Decimal(0))
        )
        context = {
            "total_short": data.get("short_total"),
            "full_return_amount": data.get("full_return_total"),
            "full_return_unique_pharmacy": data.get("full_return_unique_pharmacy"),
            "partial_return_amount": data.get("partial_return_total"),
            "partial_return_unique_pharmacy": data.get("partial_return_unique_pharmacy"),
            "sub_top_sheet_items": self.get_sub_top_sheet_short_return_data()
        }
        return short_return_logs.exists(), context

    def get_short_amount(self):
        return self.total_data.get('total_short_amount', 0.00)

    def get_return_amount(self):
        return self.total_data.get('total_return_amount', 0.00)

    def get_total_invoices_and_amount(self):
        invoices = InvoiceGroupDeliverySheet.objects.values('id').filter(pk=self.pk).annotate(
            total_invoices=Count('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__id'),
            total_amount=Sum(
                Coalesce('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__sub_total', decimal.Decimal(0)))
        )
        context = {
            'total_invoices': invoices[0]['total_invoices'],
            'total_amount': invoices[0]['total_amount']
        }
        return context

    @property
    def info(self):
        """
        Get info of invoice group delivery sheet
        Returns:
        number of invoice, invoice amount, short_amount, return_amount,
        pending return amount, partial return amount, full return amount,
        number of unique pharmacy, partial return unique pharmacy, full return unique pharmacy
        """
        top_sheet = self.__class__.objects.filter(pk=self.pk)
        invoices = top_sheet.aggregate(
            total_invoices=Count('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__id'),
            total_invoice_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__status=Status.ACTIVE,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__sub_total') + F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__round_discount') - F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__discount') - F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__additional_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0))
        )
        short_return = top_sheet.aggregate(
            total_short_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0)),
            total_return_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount')+ F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0)),
            total_pending_short_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount')+ F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0)),
            total_pending_return_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.DRAFT,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount')+ F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0)),
            total_partial_return_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__current_order_status=OrderTrackingStatus.PARITAL_DELIVERED,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount')+ F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0)),
            total_full_return_amount=Coalesce(Sum(Case(When(
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
                delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__current_order_status=OrderTrackingStatus.FULL_RETURNED,
                then=F('delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount')+ F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=0, output_field=DecimalField())), decimal.Decimal(0)),
        )
        total_unique_pharmacy = top_sheet.filter(
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
        ).aggregate(
            total_unique_pharmacy=Count(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__order_by_organization__id',
                distinct=True
            )
        )
        total_partial_return_unique_pharmacy = top_sheet.filter(
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__current_order_status=OrderTrackingStatus.PARITAL_DELIVERED
        ).aggregate(
            total_partial_return_unique_pharmacy=Count(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__order_by_organization__id',
                distinct=True
            )
        )
        total_full_return_unique_pharmacy = top_sheet.filter(
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE,
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN,
            delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__current_order_status=OrderTrackingStatus.FULL_RETURNED
        ).aggregate(
            total_full_return_unique_pharmacy=Count(
                'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__order_by_organization__id',
                distinct=True
            )
        )

        unique_pharmacy = {
            **total_unique_pharmacy,
            **total_partial_return_unique_pharmacy,
            **total_full_return_unique_pharmacy
        }
        # get all the data and append it to a dict
        data = {
            **invoices,
            **short_return,
            **unique_pharmacy
        }
        return data

    @property
    def is_short_return_amount_mismatched(self):
        top_sheet = self.__class__.objects.filter(pk=self.pk)
        # calculate the total short return amount for the top sheet
        top_sheet_calculated_short_return = top_sheet.aggregate(
            total_return=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0), output_field=FloatField()),
            total_short=Coalesce(Sum(Case(When(
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__short_return_amount') + F(
                    'delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0), output_field=FloatField()),
        )
        top_sheet_short_return = {}
        total_data = top_sheet.values('total_data').first().get('total_data')
        top_sheet_short_return["total_return"] = float(total_data['total_return_amount'])
        top_sheet_short_return["total_short"] = float(total_data['total_short_amount'])
        # calculate the total short return amount for the delivery sheet invoice group
        delivery_sheet_invoice_group_ids = list(
            top_sheet.values_list('delivery_sheet_items__delivery_sheet_invoice_groups__id', flat=True))
        delivery_sheet_invoice_group = DeliverySheetInvoiceGroup.objects.filter(pk__in=delivery_sheet_invoice_group_ids)
        delivery_sheet_invoice_group_calculated_short_return = delivery_sheet_invoice_group.aggregate(
            total_return=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.RETURN) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F(
                    'invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0), output_field=FloatField()),
            total_short=Coalesce(Sum(Case(When(
                Q(invoice_group__invoice_groups__type=ShortReturnLogType.SHORT) &
                Q(invoice_group__invoice_groups__status=Status.ACTIVE),
                then=F('invoice_group__invoice_groups__short_return_amount') + F(
                    'invoice_group__invoice_groups__round_discount')
            ), default=decimal.Decimal(0))), decimal.Decimal(0), output_field=FloatField()),
        )
        delivery_sheet_invoice_group_short_return = delivery_sheet_invoice_group.aggregate(
            total_return=Coalesce(Sum('total_return'), decimal.Decimal(0), output_field=FloatField()),
            total_short=Coalesce(Sum('total_short'), decimal.Decimal(0), output_field=FloatField()),
        )
        return top_sheet_calculated_short_return != top_sheet_short_return or delivery_sheet_invoice_group_calculated_short_return != delivery_sheet_invoice_group_short_return


class DeliverySheetItem(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateField()
    order_by_organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        related_name='invoice_group_delivery_sheet_items',
        help_text='Organization of a delivery sheet item'
    )
    invoice_group_delivery_sheet = models.ForeignKey(
        InvoiceGroupDeliverySheet,
        models.DO_NOTHING,
        related_name='delivery_sheet_items',
        help_text='Invoice group delivery sheet instance'
    )
    invoice_group_delivery_sub_sheet = models.ForeignKey(
        InvoiceGroupDeliverySheet,
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='sub_top_sheet_delivery_sheet_items',
        help_text='Invoice group delivery sheet instance for sub top sheet'
    )
    total_unique_item_order = models.IntegerField(default=0)
    total_unique_item_short = models.IntegerField(default=0)
    total_unique_item_return = models.IntegerField(default=0)
    total_item_order = models.IntegerField(default=0)
    total_item_short = models.IntegerField(default=0)
    total_item_return = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Delivery Sheet Item"
        verbose_name_plural = "Delivery Sheet Items"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.order_by_organization_id)


class DeliverySheetInvoiceGroup(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateField()
    invoice_group = models.ForeignKey(
        OrderInvoiceGroup,
        models.DO_NOTHING,
        related_name='delivery_sheet_invoice_groups',
        help_text='Invoice group instance'
    )
    delivery_sheet_item = models.ForeignKey(
        DeliverySheetItem,
        models.DO_NOTHING,
        related_name='delivery_sheet_invoice_groups',
        help_text='Delivery sheet item'
    )
    sub_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    grand_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    round_discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    additional_discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    additional_cost = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_short = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_return = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)

    class Meta:
        verbose_name = "Delivery Sheet Invoice Group"
        verbose_name_plural = "Delivery Sheet Invoice Groups"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.invoice_group_id)


class Wishlist(CreatedAtUpdatedAtBaseModelWithOrganization):
    total_item = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: Total Items: {}".format(self.id, self.total_item)

    def update_wishlist_item_count(self):
        self.total_item = self.wishlist_items.filter(
            status=Status.ACTIVE
        ).count()
        self.save()


class WishlistItem(CreatedAtUpdatedAtBaseModelWithOrganization):
    stock = models.ForeignKey(
        Stock,
        models.DO_NOTHING,
        null=False, blank=False,
        related_name='wishlist_items'
    )
    wishlist = models.ForeignKey(
        Wishlist,
        models.DO_NOTHING,
        null=False, blank=False,
        related_name='wishlist_items'
    )
    product_name = models.CharField(max_length=512, null=False, blank=False)
    suggested_price = models.DecimalField(default=0.00, max_digits=19, decimal_places=3, null=True, blank=True)
    sell_quantity_per_week = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.stock)


class TopSheetSubTopSheet(CreatedAtUpdatedAtBaseModelWithOrganization):
    top_sheet = models.ForeignKey(
        InvoiceGroupDeliverySheet,
        models.DO_NOTHING,
        related_name='top_sheets'
    )
    sub_top_sheet = models.ForeignKey(
        InvoiceGroupDeliverySheet,
        models.DO_NOTHING,
        related_name='sub_top_sheets'
    )

    class Meta:
        verbose_name = "TopSheetSubTopSheet"
        verbose_name_plural = "TopSheetSubTopSheets"

    def __str__(self):
        return f"{self.top_sheet_id} - {self.sub_top_sheet_id}"


pre_save.connect(store_old_instance_value, sender=OrderInvoiceGroup)
pre_save.connect(pre_save_short_return_item, sender=ShortReturnItem)
pre_save.connect(pre_save_short_return_log, sender=ShortReturnLog)
post_save.connect(post_save_short_return_log, sender=ShortReturnLog)
post_save.connect(post_save_order_invoice_group, sender=OrderInvoiceGroup)
post_save.connect(post_save_invoice_group_delivery_sheet, sender=InvoiceGroupDeliverySheet)
