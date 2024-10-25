import time
from datetime import datetime
from decimal import Decimal

from validator_collection import checkers

from django.db import models
from django.db.models import Sum, FloatField, F, DecimalField, Count, IntegerField, Q
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save, pre_save
from django.utils.translation import gettext as _
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from enumerify import fields
from simple_history.models import HistoricalRecords

from common.models import CreatedAtUpdatedAtBaseModelWithOrganization, CreatedAtUpdatedAtBaseModel
from common.fields import JSONTextField
from common.enums import Status
from common.helpers import custom_elastic_rebuild
from common.utils import DistinctSum
from common.cache_keys import PERSON_ORG_SUPPLIER_STOCK_RATE_AVG
from common.utils import DistinctSum

from .enums import (
    ProcureType,
    ProcureItemType,
    RateStatus,
    RecommendationPriority,
    ProcureIssueType,
    PredictionItemMarkType,
    ProcureStatus,
    ProcurePlatform,
    ReturnReason,
    ReturnCurrentStatus,
    ReturnSettlementMethod,
    ProcurePaymentMethod, CreditStatusChoices,
)
from .signals import (
    post_save_procure_item,
    pre_save_procure_item,
    pre_save_procure,
    post_save_procure_issue_log,
    post_save_procure,
    post_save_prediction_item_mark,
    post_save_procure_status,
    pre_save_procure_group,
)

class PurchasePrediction(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    label = models.CharField(max_length=512, null=True, blank=True,)
    prediction_file = models.ForeignKey(
        'core.ScriptFileStorage',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='stocks_predictions',
    )
    is_locked = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Purchase Prediction"
        verbose_name_plural = "Purchase Predictions"

        unique_together = ["prediction_file"]

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.organization_id)


class PredictionItem(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateField()
    stock = models.ForeignKey(
        'pharmacy.Stock',
        models.DO_NOTHING,
        related_name='stocks_prediction_items'
    )
    product_name = models.CharField(max_length=512, blank=True, null=True)
    company_name = models.CharField(max_length=128, blank=True, null=True)
    purchase_prediction = models.ForeignKey(
        PurchasePrediction,
        models.DO_NOTHING,
        related_name='prediction_items'
    )
    # Product rate from box
    mrp = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # Price after applying discount
    sale_price = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    avg_purchase_rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    lowest_purchase_rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    highest_purchase_rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # Margin with avg
    margin = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    product_visibility_in_catelog = models.CharField(max_length=24, blank=True, null=True)
    old_stock = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    sold_quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    purchase_quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    short_quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    return_quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    new_stock = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    prediction = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    new_order = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # D3
    suggested_purchase_quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # D1
    suggested_min_purchase_quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    has_min_purchase_quantity = models.BooleanField(default=False)
    purchase_order = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    marked_status = fields.SelectIntegerField(
        blueprint=PredictionItemMarkType,
        default=PredictionItemMarkType.UN_MARK,
    )
    # RAVG
    real_avg = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # EMP_ID
    assign_to = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='prediction_item_assign_to'
    )
    # 3D
    sale_avg_3d = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # WRATE
    worst_rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    # TEAM
    team = models.CharField(max_length=24, blank=True, null=True)
    # Index from file for finding specific item and avoid duplication
    index = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Prediction Item"
        verbose_name_plural = "Prediction Items"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.organization_id)

    def get_total_purchase_order_qty(self):
        procure_items = self.procure_items.filter(
            status=Status.ACTIVE
        ).aggregate(
            total_qty=Coalesce(Sum(
                'quantity',
                output_field=FloatField()
            ), 0.00)
        )
        return procure_items.get('total_qty', 0)

    def get_suppliers_by_days(self, days = 90):
        from django.utils import timezone
        from datetime import date, datetime, time
        from dateutil.relativedelta import relativedelta

        from common.enums import Status
        from pharmacy.enums import StockIOType, PurchaseType, PurchaseOrderStatus
        from pharmacy.models import StockIOLog

        end_date = str(date.today() + relativedelta(days=-1))
        start_date = str(date.today() + relativedelta(days=-(days + 1)))
        start_date = datetime.combine(
            datetime.strptime(start_date, '%Y-%m-%d'), time.min)
        end_date = datetime.combine(
            datetime.strptime(end_date, '%Y-%m-%d'), time.max)
        start_date = timezone.make_aware(
            start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(
            end_date, timezone.get_current_timezone())

        io_logs = StockIOLog.objects.filter(
            stock__id=self.stock_id,
            status=Status.ACTIVE,
            organization__id=self.organization_id,
            type=StockIOType.INPUT,
            purchase__status=Status.ACTIVE,
            purchase__purchase_type=PurchaseType.PURCHASE,
            purchase__is_sales_return=False,
            purchase__purchase_order_status=PurchaseOrderStatus.DEFAULT,
            purchase__purchase_date__range=[start_date, end_date],
            purchase__person_organization_supplier__isnull=False
        ).values(
            'purchase__person_organization_supplier_id',
            'purchase__person_organization_supplier__company_name',
            'purchase__person_organization_supplier__phone'
        ).annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')
        return io_logs

    def get_supplier_avg_rate(self, supplier_alias):
        from pharmacy.helpers import get_average_purchase_price
        from pharmacy.tasks import populate_stock_supplier_avg_rate_cache

        base_cache_key = PERSON_ORG_SUPPLIER_STOCK_RATE_AVG
        cache_key = f"{base_cache_key}_{self.stock_id}_{supplier_alias}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        if checkers.is_uuid(supplier_alias):
            # populate_stock_supplier_avg_rate_cache(self.stock_id)
            try:
                return get_average_purchase_price(
                    stock_id=self.stock_id,
                    person_organization_supplier_alias=supplier_alias
                )
            except:
                return None
        return None


class PredictionItemSupplier(CreatedAtUpdatedAtBaseModelWithOrganization):
    prediction_item = models.ForeignKey(
        PredictionItem, models.DO_NOTHING,
        related_name='prediction_item_suggestions'
    )
    supplier = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='prediction_item_suppliers'
    )
    rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    priority = fields.SelectIntegerField(
        blueprint=RecommendationPriority,
        default=RecommendationPriority.OTHER,
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Prediction Item Supplier"
        verbose_name_plural = "Prediction Item Suppliers"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.prediction_item_id, self.supplier_id)


class PredictionItemMark(CreatedAtUpdatedAtBaseModelWithOrganization):
    prediction_item = models.ForeignKey(
        PredictionItem, models.DO_NOTHING,
        related_name='prediction_item_marks'
    )
    supplier = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='prediction_item_mark_suppliers'
    )
    rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    type = fields.SelectIntegerField(
        blueprint=PredictionItemMarkType,
        default=PredictionItemMarkType.MARK,
    )
    employee = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='prediction_item_mark_employees'
    )
    remarks = models.CharField(max_length=512, blank=True, null=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Prediction Item Mark"
        verbose_name_plural = "Prediction Item Marks"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.prediction_item_id, self.supplier_id)


class Procure(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    supplier = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='procure_suppliers'
    )
    contractor = models.ForeignKey(
        'core.PersonOrganization',
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        related_name='procure_contractors'
    )
    sub_total = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    discount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    employee = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='procure_employees'
    )
    type = fields.SelectIntegerField(
        blueprint=ProcureType,
        default=ProcureType.DEFAULT,
    )
    operation_start = models.DateTimeField(blank=True, null=True)
    operation_end = models.DateTimeField(blank=True, null=True)
    remarks = models.CharField(max_length=512, blank=True, null=True)
    invoices = models.CharField(max_length=1024, blank=True, null=True)
    geo_location_data = JSONTextField(blank=True, null=True, default='{}')
    requisition = models.ForeignKey(
        'pharmacy.Purchase',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='procure_requisitions'
    )
    copied_from = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, default=None)
    current_status = fields.SelectIntegerField(
        blueprint=ProcureStatus,
        default=ProcureStatus.DRAFT,
        help_text='Define current status of procure'
    )
    estimated_collection_time = models.DateTimeField(blank=True, null=True)
    medium = fields.SelectIntegerField(
        blueprint=ProcurePlatform,
        default=ProcurePlatform.PHYSICAL,
    )
    shop_name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name=('shop name'),
        help_text='The name will be user for print header'
    )
    procure_group = models.ForeignKey(
        'ProcureGroup',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        verbose_name='procure group',
        related_name='procure_group_procures'
    )
    credit_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    paid_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    is_credit_purchase = models.BooleanField(default=False)
    credit_payment_term = models.PositiveIntegerField(default=0)
    credit_payment_term_date = models.DateField(blank=True, null=True)
    credit_cost_percentage = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    credit_cost_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    open_credit_balance = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    history = HistoricalRecords()

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Procure"
        verbose_name_plural = "Procures"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.supplier_id, self.employee_id)

    @property
    def is_procure_date_advanced(self):
        return self.created_at.date() < self.date.date()

    def complete_purchase(self, date, organization_id, user):
        from pharmacy.helpers import (
            create_requisition_for_procure,
            create_purchase_or_order_for_procure,
        )
        from .helpers import send_procure_alert_to_slack

        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

        # _datetime_now = datetime.strptime(
        #     time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
        _datetime_now = date

        if settings.DEBUG:
            store_point_id = 94
            department_id = 9
        else:
            store_point_id = 408
            department_id = 9

        procure_items = list(ProcureItem.objects.filter(procure__id=self.id).values(
            'stock',
            'quantity',
            'rate',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__conversion_factor',
        ))
        # Create requisition
        if not self.requisition_id:
            requisition_instance = create_requisition_for_procure(
                _datetime_now,
                self,
                procure_items,
                organization_id,
                user,
                store_point_id,
                department_id,
            )
            self.requisition_id = requisition_instance.id
            self.save(update_fields=['requisition', ])
        else:
            requisition_instance = self.requisition
        # Create purchase order
        purchase_order_instance = create_purchase_or_order_for_procure(
            _datetime_now,
            self,
            procure_items,
            organization_id,
            user,
            store_point_id,
            requisition_instance.id,
            Status.PURCHASE_ORDER
        )
        # Create purchase
        purchase_instance = create_purchase_or_order_for_procure(
            _datetime_now,
            self,
            procure_items,
            organization_id,
            user,
            store_point_id,
            purchase_order_instance.id,
            Status.ACTIVE
        )
        requisition_id = requisition_instance.id
        purchase_order_id = purchase_order_instance.id
        purchase_id = purchase_instance.id
        custom_elastic_rebuild(
            'pharmacy.models.Purchase',
            {
                'pk__in': [
                    requisition_id,
                    purchase_order_id,
                    purchase_id,
                ]
            }
        )
        message = f"Completed Requisition (#{requisition_id}), Purchase Order (#{purchase_order_id}) and Purchase (#{purchase_id}) for Procure Purchase (#{self.id}) by {purchase_instance.person_organization_receiver.get_full_name()}."
        send_procure_alert_to_slack(message)

    def delete_related_purchase(self, updated_by_id):
        from pharmacy.models import Purchase, PurchaseRequisition
        from .helpers import send_procure_alert_to_slack

        requisition = Purchase.objects.get(pk=self.requisition_id)

        purchase_requisitions_connector = PurchaseRequisition.objects.filter(
            status=Status.ACTIVE,
            requisition__id=self.requisition_id,
            purchase__status=Status.PURCHASE_ORDER
        )
        purchase_instance_id_for_es_update = [
            self.requisition_id
        ]
        purchase_order_id_list = []
        purchase_id_list = []

        for item in purchase_requisitions_connector:
            purchases = Purchase.objects.filter(copied_from__id=item.purchase_id).only('status', 'id')
            for purchase in purchases:
                purchase.status = Status.INACTIVE
                purchase.updated_by_id = updated_by_id
                purchase.save(update_fields=['status', 'updated_by_id',])
                purchase_order_id_list.append(purchase.id)
            item.purchase.status = Status.INACTIVE
            item.purchase.updated_by_id = updated_by_id
            item.purchase.save(update_fields=['status', 'updated_by_id',])
            item.status = Status.INACTIVE
            item.updated_by_id = updated_by_id
            item.save(update_fields=['status', 'updated_by_id',])
            purchase_id_list.append(item.purchase_id)

        # purchase_order_pk_list = PurchaseRequisition.objects.filter(
        #     status=Status.ACTIVE,
        #     requisition__id=self.requisition_id,
        #     purchase__status=Status.PURCHASE_ORDER
        # ).values_list('purchase_id', flat=True)
        # purchase_orders = Purchase.objects.filter(pk__in=purchase_order_pk_list).only('status')
        requisition.status = Status.INACTIVE
        requisition.updated_by_id = updated_by_id
        requisition.save(update_fields=['status', 'updated_by_id',])
        self.requisition = None
        self.updated_by_id = updated_by_id
        self.save(update_fields=['requisition', 'updated_by_id',])
        purchase_order_ids = ",".join(map(str, purchase_order_id_list))
        purchase_ids = ",".join(map(str, purchase_id_list))
        message = f"Deleted linked Requisition (#{requisition.id}), Purchase Order (#{purchase_order_ids}), Purchase (#{purchase_ids}) for Procure Purchase (#{self.id}) by {self.employee.get_full_name()}."
        send_procure_alert_to_slack(message)
        purchase_instance_id_for_es_update += purchase_order_id_list + purchase_id_list
        custom_elastic_rebuild(
            'pharmacy.models.Purchase',
            {'pk__in': purchase_instance_id_for_es_update}
        )

    def get_procure_items(self):
        return self.procure_items.filter(status=Status.ACTIVE)

    def clone_procure_with_updated_subtotal(self, request):
        procure = self
        procure_items = procure.get_procure_items()
        if procure_items.exists():
            grand_total = procure_items.aggregate(
                grand_total=Sum(
                    F('quantity') * F('rate'),
                    output_field=DecimalField()
                )
            ).get('grand_total', Decimal(0.00))
            new_procure = Procure.objects.create(
                date=procure.date,
                supplier=procure.supplier,
                contractor=procure.contractor,
                sub_total=grand_total,
                discount=procure.discount,
                employee=procure.employee,
                type=procure.type,
                operation_start=procure.operation_start,
                operation_end=procure.operation_end,
                remarks=procure.remarks,
                invoices=procure.invoices,
                geo_location_data=procure.geo_location_data,
                requisition=procure.requisition,
                copied_from=procure,
                current_status=procure.current_status,
                estimated_collection_time=procure.estimated_collection_time,
                medium=procure.medium,
                shop_name=procure.shop_name,
                procure_group=procure.procure_group,
                organization_id=request.user.organization_id,
                entry_by_id=request.user.id,
                updated_by_id=None,
            )
            for item in procure_items:
                item.procure = new_procure
                item.save(update_fields=['procure'])
            procure.status = Status.INACTIVE
            procure.save(update_fields=['status'])
            return new_procure
        else:
            procure.status = Status.INACTIVE
            procure.save(update_fields=['status'])
        return procure

    def get_all_previous_instances(self):
        procure = Procure.objects.get(id=self.id)
        previous_instances = [procure]
        while procure.copied_from is not None:
            procure = procure.copied_from
            previous_instances.append(procure)

        return previous_instances


class ProcureItem(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateField()
    stock = models.ForeignKey(
        'pharmacy.Stock',
        models.DO_NOTHING,
        related_name='stocks_procure_items'
    )
    product_name = models.CharField(max_length=512, blank=True, null=True)
    company_name = models.CharField(max_length=128, blank=True, null=True)
    rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    type = fields.SelectIntegerField(
        blueprint=ProcureItemType,
        default=ProcureItemType.IN,
    )
    procure = models.ForeignKey(
        Procure,
        models.DO_NOTHING,
        related_name='procure_items'
    )
    prediction_item = models.ForeignKey(
        PredictionItem,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='procure_items',
    )
    rate_status = fields.SelectIntegerField(
        blueprint=RateStatus,
        default=RateStatus.OK,
    )

    class Meta:
        verbose_name = "Procure Item"
        verbose_name_plural = "Procure Items"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.organization_id)

    def clone_procure_item_with_new_quantity(self, quantity, request):
        procure_item = self
        new_procure_item = ProcureItem.objects.create(
            status=Status.ACTIVE,
            date=procure_item.date,
            stock=procure_item.stock,
            product_name=procure_item.product_name,
            company_name=procure_item.company_name,
            rate=procure_item.rate,
            quantity=quantity,
            type=procure_item.type,
            procure=procure_item.procure,
            prediction_item=procure_item.prediction_item,
            rate_status=procure_item.rate_status,
            organization_id=request.user.organization_id,
            entry_by_id=request.user.id,
            updated_by_id=None,
        )
        procure_item.status = Status.INACTIVE
        procure_item.save(update_fields=['status'])
        return new_procure_item

class ProcureIssueLog(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    supplier = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        related_name='procure_issue_suppliers'
    )
    employee = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='procure_issue_employees'
    )
    type = fields.SelectIntegerField(
        blueprint=ProcureIssueType,
        default=ProcureIssueType.OTHER,
    )
    stock = models.ForeignKey(
        'pharmacy.Stock',
        models.DO_NOTHING,
        related_name='stocks_procure_issue_items'
    )
    prediction_item = models.ForeignKey(
        PredictionItem,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='procure_issue_items',
    )
    remarks = models.CharField(max_length=512, blank=True, null=True)
    geo_location_data = JSONTextField(blank=True, null=True, default='{}')

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Procure Issue"
        verbose_name_plural = "Procure Issues"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.supplier_id, self.employee_id)


class ProcureGroup(CreatedAtUpdatedAtBaseModel):
    date = models.DateTimeField()
    supplier = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='procure_groups'
    )
    contractor = models.ForeignKey(
        "core.PersonOrganization",
        models.DO_NOTHING,
        related_name="contractor_procure_groups",
        null=True,
    )
    total_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    total_discount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    num_of_boxes = models.IntegerField(default=0)
    num_of_unique_boxes = models.IntegerField(default=0)

    current_status = fields.SelectIntegerField(
        blueprint=ProcureStatus,
        default=ProcureStatus.DRAFT,
        help_text='Define current status of procure'
    )

    requisition = models.ForeignKey(
        'pharmacy.Purchase',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='procure_group_requisitions'
    )
    credit_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    paid_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    is_credit_purchase = models.BooleanField(default=False)
    credit_payment_term = models.PositiveIntegerField(default=0)
    credit_payment_term_date = models.DateField(blank=True, null=True)
    credit_cost_percentage = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    credit_cost_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    open_credit_balance = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    cash_commission = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    credit_status = models.CharField(
        max_length=20,
        choices=CreditStatusChoices.choices,
        default=CreditStatusChoices.UNPAID,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Procure Group"
        verbose_name_plural = "Procure Groups"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.supplier_id)

    def validate_delete(self):
        from pharmacy.models import Purchase
        has_requisition =  Purchase.objects.values_list(
            "id",
            flat=True
        ).filter(procure_requisitions__procure_group__id=self.id).exists()
        if has_requisition:
            raise ValidationError(
                {
                    "detail": "Cannot delete Procure Group as it has linked requisition."
                },
            )
        return True

    @property
    def procures(self):
        return self.procure_group_procures.filter(
            status=Status.ACTIVE
        )

    def update_group_stats(self):
        procure_queryset = Procure.objects.filter(
            status=Status.ACTIVE,
            procure_group__id=self.id,
        )
        procures = procure_queryset.values('supplier').aggregate(
            total_amount=Coalesce(Sum('sub_total'), 0.00, output_field=DecimalField()),
            total_discount=Coalesce(Sum('discount'), 0.00, output_field=DecimalField()),
        )
        procure_boxes = procure_queryset.values('supplier').aggregate(
            total_boxes=Sum(
                'procure_items__quantity',
                filter=Q(procure_items__status=Status.ACTIVE)
            ),
            total_unique_boxes=Count(
                'procure_items__stock',
                distinct=True,
                filter=Q(procure_items__status=Status.ACTIVE)
            ),
        )
        self.total_amount = procures.get('total_amount')
        self.total_discount = procures.get('total_discount')
        self.num_of_boxes = procure_boxes.get('total_boxes')
        self.num_of_unique_boxes = procure_boxes.get('total_unique_boxes')
        update_fields = []
        if procures.get('total_amount') == 0.00 and procures.get('total_discount') == 0.00:
            self.status = Status.INACTIVE
            update_fields.append('status')
        else:
            self.total_amount = procures.get('total_amount')
            self.total_discount = procures.get('total_discount')
            self.num_of_boxes = procure_boxes.get('total_boxes')
            self.num_of_unique_boxes = procure_boxes.get('total_unique_boxes')
            update_fields.extend([
                'total_amount',
                'total_discount',
                'num_of_boxes',
                'num_of_unique_boxes',
            ])
        self.save(
            update_fields=update_fields
        )
        return self

    def complete_group_purchase(self, date, organization_id, user):
        from .helpers import (
            send_procure_alert_to_slack,
            create_requisition_for_procure_group,
            create_purchase_or_order_for_procure_group,
        )
        _datetime_now = date

        if settings.DEBUG:
            store_point_id = 94
            department_id = 9
        else:
            store_point_id = 408
            department_id = 9

        procure_items = list(ProcureItem.objects.filter(
            procure__procure_group__id=self.id,
            status=Status.ACTIVE,
        ).values(
            'stock',
            'rate',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__conversion_factor',
        ).annotate(
            total_quantity=Sum('quantity')
        ))
        procures = self.procure_group_procures.filter(status=Status.ACTIVE)
        invoices = list(procures.values_list('invoices', flat=True))
        # Create requisition for procure group
        if not self.requisition_id:
            requisition_instance = create_requisition_for_procure_group(
                _datetime_now,
                self,
                procure_items,
                organization_id,
                user,
                store_point_id,
                department_id,
                invoices
            )
            self.requisition_id = requisition_instance.id
            self.save(update_fields=['requisition', ])
            procures.update(requisition=requisition_instance)
        else:
            requisition_instance = self.requisition

        # Create purchase order for procure group
        purchase_order_instance = create_purchase_or_order_for_procure_group(
            _datetime_now,
            self,
            procure_items,
            organization_id,
            user,
            store_point_id,
            requisition_instance.id,
            Status.PURCHASE_ORDER,
            invoices
        )

        # Create purchase
        purchase_instance = create_purchase_or_order_for_procure_group(
            _datetime_now,
            self,
            procure_items,
            organization_id,
            user,
            store_point_id,
            purchase_order_instance.id,
            Status.ACTIVE,
            invoices
        )
        requisition_id = requisition_instance.id
        purchase_order_id = purchase_order_instance.id
        purchase_id = purchase_instance.id
        custom_elastic_rebuild(
            'pharmacy.models.Purchase',
            {
                'pk__in': [
                    requisition_id,
                    purchase_order_id,
                    purchase_id,
                ]
            }
        )
        message = f"Completed Requisition (#{requisition_id}), Purchase Order (#{purchase_order_id}) and Purchase (#{purchase_id}) for Procure Group Purchase (#{self.id}) by {purchase_instance.person_organization_receiver.get_full_name()}."
        send_procure_alert_to_slack(message)

    def delete_related_purchase_from_procure_group(self, updated_by_id):
        from pharmacy.models import Purchase, PurchaseRequisition
        from .helpers import send_procure_alert_to_slack

        procures = self.procure_group_procures.filter(status=Status.ACTIVE)

        requisition = Purchase.objects.get(pk=self.requisition_id)

        purchase_requisitions_connector = PurchaseRequisition.objects.filter(
            status=Status.ACTIVE,
            requisition__id=self.requisition_id,
            purchase__status=Status.PURCHASE_ORDER
        )
        purchase_instance_id_for_es_update = [
            self.requisition_id
        ]
        purchase_order_id_list = []
        purchase_id_list = []

        for item in purchase_requisitions_connector:
            purchases = Purchase.objects.filter(copied_from__id=item.purchase_id).only('status', 'id')
            for purchase in purchases:
                purchase.status = Status.INACTIVE
                purchase.updated_by_id = updated_by_id
                purchase.save(update_fields=['status', 'updated_by_id',])
                purchase_order_id_list.append(purchase.id)
            item.purchase.status = Status.INACTIVE
            item.purchase.updated_by_id = updated_by_id
            item.purchase.save(update_fields=['status', 'updated_by_id',])
            item.status = Status.INACTIVE
            item.updated_by_id = updated_by_id
            item.save(update_fields=['status', 'updated_by_id',])
            purchase_id_list.append(item.purchase_id)

        requisition.status = Status.INACTIVE
        requisition.updated_by_id = updated_by_id
        requisition.save(update_fields=['status', 'updated_by_id',])
        self.requisition = None
        self.updated_by_id = updated_by_id
        self.save(update_fields=['requisition', 'updated_by_id',])
        procures.update(requisition=None, updated_by_id=updated_by_id)
        purchase_order_ids = ",".join(map(str, purchase_order_id_list))
        purchase_ids = ",".join(map(str, purchase_id_list))
        message = f"Deleted linked Requisition (#{requisition.id}), Purchase Order (#{purchase_order_ids}), Purchase (#{purchase_ids}) for Procure Group Purchase (#{self.id}) by {self.entry_by.get_full_name()}."
        send_procure_alert_to_slack(message)
        purchase_instance_id_for_es_update += purchase_order_id_list + purchase_id_list
        custom_elastic_rebuild(
            'pharmacy.models.Purchase',
            {'pk__in': purchase_instance_id_for_es_update}
        )

class ProcureStatus(CreatedAtUpdatedAtBaseModel):
    """
    Procure Status
    """
    date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date time for status changed'
    )
    current_status = fields.SelectIntegerField(
        blueprint=ProcureStatus,
        default=ProcureStatus.DRAFT,
        help_text='Define current status of procure'
    )
    procure = models.ForeignKey(
        Procure, models.DO_NOTHING,
        related_name='procure_status',
        help_text='The procure for tracking status')
    remarks = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Procure Status"
        verbose_name_plural = "Procure Statuses"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.procure_id, self.current_status)


class ProcureReturn(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    reason = models.CharField(
        max_length=20,
        choices=ReturnReason.choices,
        default=ReturnReason.OTHER,
        blank=True,
    )
    reason_note = models.CharField(
        max_length=250,
        blank=True,
    )
    procure = models.ForeignKey(
        Procure,
        on_delete=models.DO_NOTHING,
        related_name="procure_returns",
    )
    product_name = models.CharField(
        max_length=255,
        blank=True,
    )
    total_return_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    total_settled_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    current_status = models.CharField(
        max_length=20,
        choices=ReturnCurrentStatus.choices,
        default=ReturnCurrentStatus.PENDING,
        blank=True,
    )
    settlement_method = models.CharField(
        max_length=30,
        choices=ReturnSettlementMethod.choices,
        default=ReturnSettlementMethod.CASH,
        blank=True,
    )
    full_settlement_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    employee = models.ForeignKey(
        "core.PersonOrganization",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="employee_procure_returns",
    )
    contractor = models.ForeignKey(
        "core.PersonOrganization",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="contractor_procure_returns",
    )
    stock = models.ForeignKey(
        "pharmacy.Stock",
        on_delete=models.DO_NOTHING,
        related_name="stock_procure_returns",
    )
    quantity = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    rate = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )

    def __str__(self):
        return f"{self.procure} {self.date}"

    class Meta:
        verbose_name_plural = "Procure Returns"


class ReturnSettlement(CreatedAtUpdatedAtBaseModel):
    procure_return = models.ForeignKey(
        ProcureReturn,
        on_delete=models.DO_NOTHING,
        related_name="procure_return_settlements",
    )
    date = models.DateTimeField()
    settlement_method = models.CharField(
        max_length=30,
        choices=ReturnSettlementMethod.choices,
        default=ReturnSettlementMethod.CASH,
        blank=True,
    )
    settlement_method_reference = models.CharField(
        max_length=250,
        blank=True,
    )
    amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    employee = models.ForeignKey(
        "core.PersonOrganization",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="employee_return_settlements",
    )

    def __str__(self):
        return f"{self.procure_return} {self.date}"

    class Meta:
        verbose_name_plural = "Procure Return Settlements"


class ProcurePayment(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
    )
    method = models.CharField(
        max_length=20,
        choices=ProcurePaymentMethod.choices,
        default=ProcurePaymentMethod.CASH,
    )
    method_reference = models.CharField(max_length=255, blank=True,)
    procure = models.ForeignKey(
        Procure,
        models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="procure_payments",
    )
    procure_group = models.ForeignKey(
        ProcureGroup,
        models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="procure_group_payments",
    )
    history = HistoricalRecords()

    def __str__(self):
        return f"Payment for {self.procure}"


# Connect all signals here
post_save.connect(post_save_procure_item, sender=ProcureItem)
pre_save.connect(pre_save_procure_item, sender=ProcureItem)
pre_save.connect(pre_save_procure, sender=Procure)
post_save.connect(post_save_procure, sender=Procure)
post_save.connect(post_save_procure_issue_log, sender=ProcureIssueLog)
post_save.connect(post_save_prediction_item_mark, sender=PredictionItemMark)
post_save.connect(post_save_procure_status, sender=ProcureStatus)
pre_save.connect(pre_save_procure_group, sender=ProcureGroup)
