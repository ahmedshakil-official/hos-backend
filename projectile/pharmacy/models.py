# for python3 compatibility
from __future__ import unicode_literals, division
import uuid, os, decimal, logging
from enumerify import fields
from datetime import datetime, timedelta, date, time, timezone as DTTZ
from dateutil.relativedelta import relativedelta
from validator_collection import checkers
import pandas as pd

from django.utils.timezone import timezone
from django.utils import timezone as django_timezone
from django.db.models import Q
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, When, Case, Value, Q, FloatField, Subquery
from django.db.models.signals import post_delete, post_save, pre_save
from django.db.models.aggregates import Sum, Count, Avg
from django.db.models.functions import Coalesce, Cast
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from common.validators import admin_validate_unique_name_with_org, positive_non_zero
from common.helpers import custom_elastic_rebuild
from common.enums import Status, DiscardType
from common.models import (
    CreatedAtUpdatedAtBaseModel,
    NameSlugDescriptionBaseOrganizationWiseModel,
    NameSlugDescriptionBaseModel,
    CreatedAtUpdatedAtBaseModelWithOrganization,
    FileStorage,
)
from common.cache_keys import (
    STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX,
    CUSTOMER_ORG_NON_GROUP_ORDER_GRAND_TOTAL_CACHE_KEY_PREFIX,
    CUSTOMER_ORG_DELIVERY_COUPON_AVAILABILITY_CACHE_KEY_PREFIX,
)
from common.utils import DistinctSum, Round
from common.tasks import cache_expire_list, cache_expire
from common.fields import TimestampImageField, JSONTextField, TimestampVersatileImageField
from core.enums import (
    PersonGroupType,
    PriceType,
    VatTaxStatus,
    AllowOrderFrom,
    FilePurposes,
)
from core.models import Organization, PersonOrganization
from core.models import Person, Department
from ecommerce.enums import ShortReturnLogType, FailedDeliveryReason

from .signals import (
    post_delete_stock_io_log,
    post_save_purchase,
    pre_save_product,
    post_save_product,
    post_save_store_point,
    post_save_employee_account_access,
    pre_save_stock,
    pre_stock_adjustment,
    pre_save_stock_io_log,
    pre_save_stock_transfer,
    post_save_employee_store_point_access,
    post_save_order_tracking,
    post_save_stock_reminder,
    post_save_logo_image,
)
from .enums import (
    StorePointType,
    StockIOType,
    ProductGroupType,
    SalesType,
    SalesInactiveType,
    TransferStatusType,
    PurchaseType,
    PurchaseOrderStatus,
    DisbursementFor,
    AdjustmentType,
    SalesModeType,
    GlobalProductCategory,
    DataEntryStatus,
    DistributorOrderType,
    OrderTrackingStatus,
    SystemPlatforms,
    UnitType,
    DamageProductType,
    RecheckProductType,
)

logger = logging.getLogger(__name__)
class ProductForm(NameSlugDescriptionBaseOrganizationWiseModel):

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{} - {}".format(self.pk, self.name)


class ProductManufacturingCompany(NameSlugDescriptionBaseOrganizationWiseModel):
    logo = TimestampVersatileImageField(
        upload_to='logo/images',
        blank=True,
        null=True
    )

    @property
    def image_set(self):
        from versatileimagefield.utils import (
            build_versatileimagefield_url_set,
            get_rendition_key_set,
            validate_versatileimagefield_sizekey_list
        )
        sizes = validate_versatileimagefield_sizekey_list(get_rendition_key_set("logo_images"))
        image_set = build_versatileimagefield_url_set(self.logo, sizes)
        return image_set

    class Meta:
        verbose_name_plural = "Product manufacturing companies"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{} - {}".format(self.pk, self.name)


class ProductGeneric(NameSlugDescriptionBaseOrganizationWiseModel):
    name = models.CharField(max_length=1024)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{} - {}".format(self.pk, self.name)


class ProductCategory(NameSlugDescriptionBaseOrganizationWiseModel):
    logo = TimestampVersatileImageField(
        upload_to='logo/images',
        blank=True,
        null=True
    )

    @property
    def image_set(self):
        from versatileimagefield.utils import (
            build_versatileimagefield_url_set,
            get_rendition_key_set,
            validate_versatileimagefield_sizekey_list
        )
        sizes = validate_versatileimagefield_sizekey_list(get_rendition_key_set("logo_images"))
        image_set = build_versatileimagefield_url_set(self.logo, sizes)
        return image_set

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}".format(self.name)

class ProductCompartment(NameSlugDescriptionBaseOrganizationWiseModel):
    priority = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{} - {}".format(self.pk, self.name)


class ProductGroup(NameSlugDescriptionBaseOrganizationWiseModel):

    type = fields.SelectIntegerField(
        blueprint=ProductGroupType, default=ProductGroupType.OTHER)
    logo = TimestampVersatileImageField(
        upload_to='logo/images',
        blank=True,
        null=True
    )

    @property
    def image_set(self):
        from versatileimagefield.utils import (
            build_versatileimagefield_url_set,
            get_rendition_key_set,
            validate_versatileimagefield_sizekey_list
        )
        sizes = validate_versatileimagefield_sizekey_list(get_rendition_key_set("logo_images"))
        image_set = build_versatileimagefield_url_set(self.logo, sizes)
        return image_set

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}".format(self.name)

    def clean(self):
        admin_validate_unique_name_with_org(self, type=self.type)


class ProductSubgroup(NameSlugDescriptionBaseOrganizationWiseModel):
    product_group = models.ForeignKey(
        ProductGroup, models.DO_NOTHING, related_name='subgroup_product_group')

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"{} - {}".format(self.product_group, self.name)

    def clean(self):
        admin_validate_unique_name_with_org(
            self, 'product_group', product_group=self.product_group)


class Product(NameSlugDescriptionBaseOrganizationWiseModel):
    trading_price = models.FloatField()
    purchase_price = models.FloatField()
    manufacturing_company = models.ForeignKey(
        ProductManufacturingCompany, models.DO_NOTHING, blank=True, null=True,
        related_name='product_manufacturing_company'
    )
    form = models.ForeignKey(
        ProductForm, models.DO_NOTHING, blank=True, null=True, related_name='product_form')
    subgroup = models.ForeignKey(
        ProductSubgroup, models.DO_NOTHING, blank=True, null=True, related_name='product_subgroup')
    generic = models.ForeignKey(
        ProductGeneric, models.DO_NOTHING, blank=True, null=True, related_name='product_generic')
    is_salesable = models.BooleanField(default=True)
    is_service = models.BooleanField(default=False)
    is_printable = models.BooleanField(default=True)
    primary_unit = models.ForeignKey(
        'Unit', models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='primary_unit'
    )
    secondary_unit = models.ForeignKey(
        'Unit', models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='secondary_unit'
    )
    conversion_factor = models.FloatField(
        validators=[positive_non_zero], default=1.00)
    category = models.ForeignKey(
        'ProductCategory', models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='category'
    )
    code = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text='Code of product'
    )
    species = models.CharField(
        max_length=255, blank=True,
        null=True,
        help_text='Purpose of product'
    )
    global_category = fields.SelectIntegerField(
        blueprint=GlobalProductCategory,
        default=GlobalProductCategory.DEFAULT
    )
    strength = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text='Strength(*mg) of product'
    )
    full_name = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        null=True,
        editable=False,
        help_text='Full name(name + strength) of product'
    )
    display_name = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        null=True,
    )
    pack_size = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Published/Unpublished status of a product distributor"
    )
    # Maximum order qty for customer
    order_limit_per_day = models.FloatField(default=0.00)
    order_limit_per_day_mirpur = models.FloatField(default=0.00)
    order_limit_per_day_uttara = models.FloatField(default=0.00)
    image = TimestampVersatileImageField(upload_to='product/images', blank=True, null=True)
    discount_rate = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=0.0,
        help_text="Discount rate for order"
    )
    alias_name = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        null=True,
        help_text='pseudonym/Alias of product'
    )
    # Next Day flag for e-commerce
    is_queueing_item = models.BooleanField(
        default=False,
        help_text="Next day flag for e-commerce"
    )
    order_mode = fields.SelectIntegerField(
        blueprint=AllowOrderFrom, default=AllowOrderFrom.OPEN)
    is_flash_item = models.BooleanField(
        default=False,
        help_text="Flash sale item flag"
    )
    unit_type = fields.SelectIntegerField(
        blueprint=UnitType, default=UnitType.BOX)
    compartment = models.ForeignKey(
        ProductCompartment,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='product_shelves'
    )
    minimum_order_quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - #COMPANY: {}".format(self.id, self.name, self.manufacturing_company_id)

    def get_medicine_name(self):
        if self.form is None:
            name = u"{} {}".format('', self.name)
        else:
            name = u"{} {}".format(self.form.name, self.name)
        return name.strip()

    def is_product_used(self):
        stock_io = StockIOLog.objects.filter(
            stock__product=self,
            status=Status.ACTIVE
        ).select_related(
            'stock__product'
        )
        stock = Stock.objects.filter(
            product=self,
            status=Status.ACTIVE,
            stock__gt=0
        )

        if stock_io.count() > 0 or stock.count() > 0:
            return True
        return False

    def update_queueing_item_value(self):
        stocks = Stock.objects.filter(
            organization__id=self.organization_id,
            store_point__status=Status.ACTIVE,
            status=Status.ACTIVE,
            product=self,
        )
        for stock in stocks:
            stock.save(update_fields=['orderable_stock', 'ecom_stock',])

    @property
    def manufacturing_company_name(self):
        return self.manufacturing_company.name if self.manufacturing_company_id else ""

    @property
    def generic_name(self):
        return self.generic.name if self.generic_id else ""

    @property
    def image_set(self):
        from django.conf import settings
        from versatileimagefield.utils import (
            build_versatileimagefield_url_set,
            get_rendition_key_set,
            validate_versatileimagefield_sizekey_list
        )
        sizes = validate_versatileimagefield_sizekey_list(get_rendition_key_set("product_images"))
        image_set = build_versatileimagefield_url_set(self.image, sizes)
        return image_set

    @property
    def is_ad_enabled(self):
        return self.stock_list.first().is_ad_enabled

    @property
    def priority(self):
        return self.stock_list.first().priority


    # @property
    # def discount_rate_factor(self):
    #     from common.healthos_helpers import CustomerHelper
    #     from common.helpers import get_request_object
    #     return CustomerHelper(
    #         get_request_object().user.organization_id
    #     ).get_cumulative_discount_factor()


    def expire_cache(self):
        import os
        from common.enums import PublishStatus
        stock_key_list = []
        stocks = Stock.objects.filter(
            product_id=self.id,
            status=Status.ACTIVE
        ).values_list('id', flat=True)

        for stock_id in stocks:
            stock_key_list.append('stock_instance_{}'.format(str(stock_id).zfill(12)))
            stock_key_list.append(f'{STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX}_{str(stock_id).zfill(12)}')

        if self.is_global == PublishStatus.PRIVATE and self.organization_id == int(os.environ.get('DISTRIBUTOR_ORG_ID', 303)):
            stock_key_list.append('manufacturing_company_published')
        cache_expire_list.apply_async(
            (stock_key_list, ),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )



class ProductAdditionalInfo(CreatedAtUpdatedAtBaseModel):
    product = models.OneToOneField(
        Product, models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='product_additional_info'
    )
    administration = models.TextField(
        blank=True,
        null=True,
        help_text='Way of Taking'
    )
    precaution = models.TextField(
        blank=True,
        null=True,
        help_text='Precautions & Warnings'
    )
    indication = models.TextField(
        blank=True,
        null=True,
        help_text='Indication of product'
    )
    contra_indication = models.TextField(
        blank=True,
        null=True,
        help_text='Contra-indication of product'
    )
    side_effect = models.TextField(
        blank=True,
        null=True,
        help_text='Side effects of product'
    )
    mode_of_action = models.TextField(
        blank=True,
        null=True,
        help_text='Mode of Action'
    )
    interaction = models.TextField(
        blank=True,
        null=True,
        help_text='Interaction / Connection'
    )
    adult_dose = models.TextField(
        blank=True,
        null=True,
        help_text='Adult Dose'
    )
    child_dose = models.TextField(
        blank=True,
        null=True,
        help_text='Child Dose'
    )
    renal_dose = models.TextField(
        blank=True,
        null=True,
        help_text='Renal Dose'
    )

    class Meta:
        verbose_name_plural = "Products Additional Infos"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.product)


class OrganizationWiseDiscardedProduct(CreatedAtUpdatedAtBaseModelWithOrganization):
    # base is current usage item
    product = models.ForeignKey(
        Product,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_product'
    )
    # product is edited, merged or deleted item
    parent = models.ForeignKey(
        Product,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_parent_product'
    )
    entry_type = fields.SelectIntegerField(
        blueprint=DiscardType,
        default=DiscardType.EDIT
    )

    class Meta:
        index_together = (
            'organization',
            'product',
        )
        verbose_name_plural = "Organization's Discarded Product"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}, Base: {}, Product: {}".format(
            self.organization,
            self.product,
            self.parent
        )


class Unit(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        verbose_name_plural = "Unit"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}".format(self.name)


class StorePoint(NameSlugDescriptionBaseModel):
    organization = models.ForeignKey(Organization, models.DO_NOTHING)
    phone = models.CharField(max_length=32)
    address = models.CharField(max_length=255)
    type = fields.SelectIntegerField(
        blueprint=StorePointType, default=StorePointType.PHARMACY)
    populate_global_product = models.BooleanField(
        default=False,
        help_text=_('Create stock for global products')
    )
    product_category = models.ManyToManyField(
        'ProductCategory',
        through='StoreProductCategory',
        related_name="store_point_product_category"
    )
    auto_adjustment = models.BooleanField(
        default=False,
        help_text=_('Settings for enable/disable auto adjustment')
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - #ORG: {}".format(self.id, self.name, self.organization_id)

    # get stock by product and store point
    def get_stock(self, product):

        try:
            stock = Stock.objects.get(
                store_point=self,
                product=product,
                status=Status.ACTIVE
            )
            return stock
        except (Stock.DoesNotExist, Stock.MultipleObjectsReturned):
            return None

    def get_person_organization_of_entry_by(self):
        if self.entry_by:
            try:
                person_organization = self.entry_by.person_organization.get(
                    status=Status.ACTIVE,
                    organization=self.organization,
                    person_group=PersonGroupType.EMPLOYEE
                )
            except PersonOrganization.DoesNotExist:
                person_organization = self.entry_by.person_organization.filter(
                    status=Status.ACTIVE,
                    organization=self.organization,
                    person_group__in=[
                        PersonGroupType.SYSTEM_ADMIN, PersonGroupType.OTHER]
                ).first()
            return person_organization

    def get_store_point_wise_stock_value(self):
        stock = Stock.objects.filter(
            organization=self.organization,
            status=Status.ACTIVE,
            # for all store point of an organization
            # store_point=self,
            product__is_service=False,
            stocks_io__status=Status.ACTIVE,
            stocks_io__isnull=False,
        ).values('product__subgroup__product_group__name', 'product__subgroup__product_group')
        stock = stock.annotate(
            product_price=Case(
                When(
                    organization__organizationsetting__price_type=PriceType.PRODUCT_PRICE,
                    then=F('product__purchase_price')
                ),
                When(
                    organization__organizationsetting__price_type=PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                    calculated_price__lte=0,
                    then=F('product__purchase_price')
                ),
                When(
                    organization__organizationsetting__price_type=PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                    product__purchase_price__gt=0,
                    then=F('product__purchase_price')
                ),
                default=F('calculated_price'),
            ),
            product_group=F('product__subgroup__product_group'),
            group_name=F('product__subgroup__product_group__name'),
            stock_value=Coalesce(Sum(F('stock')*F('product_price')), 0.00),
        ).order_by('product_group')
        return stock

    def delete_all_stock_io(self, exclude_filter=None):
        exclude_filter = {} if exclude_filter is None else exclude_filter
        StockIOLog.objects.filter(
            stock__store_point=self
        ).exclude(**exclude_filter).delete()
        self.description = 'this storepoint were reseted on {}', format(
            date.today())
        self.save(update_fields=['description'])

    def reset_stock(self, exclude_filter=None):
        exclude_filter = {} if exclude_filter is None else exclude_filter
        stocks = Stock.objects.filter(
            store_point=self,
        ).exclude(**exclude_filter)
        stocks.update(
            stock=0, demand=0, minimum_stock=0, rack=None, sales_rate=0,
            purchase_rate=0, order_rate=0, local_count=0, organizationwise_count=0,
            global_count=0, calculated_price=0, calculated_price_organization_wise=0,
            latest_purchase_unit=None, latest_sale_unit=None, tracked=False
        )

    def get_base_stock_adjustment(self):
        base_adjustment = StockAdjustment.objects.filter(
            store_point=self,
            organization=self.organization,
            status=Status.ACTIVE,
            adjustment_type=AdjustmentType.AUTO
        )

        if base_adjustment.exists() is False:
            base_adjustment = StockAdjustment.objects.create(
                store_point=self,
                organization_id=self.organization_id,
                status=Status.ACTIVE,
                adjustment_type=AdjustmentType.AUTO
            )
            base_adjustment.save()
            return base_adjustment

        return base_adjustment.first()

    def fix_stock_quantity(self, _filter=None):
        """[summary]
        fix stock quantity calculating io logs
        """
        _filter = {} if _filter is None else _filter
        # get queryset calculation correct stock
        io_logs = StockIOLog.objects.filter(
            Q(purchase__isnull=True) | Q(
                purchase__purchase_type=PurchaseType.PURCHASE),
            status=Status.ACTIVE,
            stock__store_point=self,
            **_filter
        ).values(
            'stock'
        ).order_by('stock').annotate(
            correct_qty=Coalesce(Sum(Case(When(type=StockIOType.INPUT, then=F('quantity')))), 0.00) -
            Coalesce(
                Sum(Case(When(type=StockIOType.OUT, then=F('quantity')))), 0.00),
        ).filter(~Q(stock__stock=F('correct_qty')))

        # Update stock quantity of stock iterating over queryset
        for item in io_logs:
            stock = Stock.objects.get(pk=item['stock'])
            stock.stock = item['correct_qty']
            stock.save(update_fields=['stock'])

class StoreProductCategory(CreatedAtUpdatedAtBaseModelWithOrganization):
    store_point = models.ForeignKey(
        StorePoint,
        models.DO_NOTHING,
        related_name="store_of_product_category"
    )
    product_category = models.ForeignKey(
        ProductCategory,
        models.DO_NOTHING,
        related_name="product_categoty_of_store"
    )

    class Meta:
        verbose_name = "Store Product Category"
        verbose_name_plural = "Stores Product Category"
        unique_together = (
            'store_point',
            'product_category',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(
            self.id, self.store_point, self.product_category)


class Stock(CreatedAtUpdatedAtBaseModelWithOrganization):
    store_point = models.ForeignKey(
        StorePoint, models.DO_NOTHING, blank=False, null=False, related_name='store_list')
    product = models.ForeignKey(
        Product, models.DO_NOTHING, related_name='stock_list')
    display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    stock = models.FloatField(default=0.00)
    demand = models.FloatField(default=0.00)
    is_service = models.BooleanField(default=False)
    is_salesable = models.BooleanField(default=True)
    auto_adjustment = models.BooleanField(default=True)
    tracked = models.BooleanField(default=False)
    minimum_stock = models.FloatField(default=0.00)
    rack = models.CharField(max_length=64, blank=True, null=True)
    sales_rate = models.FloatField(default=0.00)
    purchase_rate = models.FloatField(default=0.00)
    # Currently for last 3 purchase, this field will use for profut report
    avg_purchase_rate = models.FloatField(default=0.00)
    order_rate = models.FloatField(default=0.00)
    local_count = models.IntegerField(default=0)
    organizationwise_count = models.IntegerField(default=0)
    global_count = models.IntegerField(default=0)
    priority = models.PositiveIntegerField(default=1)
    # store product full name for ordering
    product_full_name = models.CharField(max_length=200, blank=True, null=True)
    # store product full name length for ordering
    product_len = models.IntegerField(default=0)
    calculated_price = models.FloatField(
        default=0.00,
        help_text="Rate of individual product stockpoint-wise after calculating vat, tax, discount"
    )
    calculated_price_organization_wise = models.FloatField(
        default=0.00,
        help_text="Rate of individual product organization-wise after calculating vat, tax, discount"
    )
    latest_purchase_unit = models.ForeignKey(
        Unit,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='latest_purchase_unit',
        verbose_name=('latest purchase unit'),
    )
    latest_sale_unit = models.ForeignKey(
        Unit,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='latest_sale_unit',
        verbose_name=('latest sale unit'),
    )
    discount_margin = models.FloatField(
        default=0.0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text=_('discount margin as percentage(%)')
    )
    purchase_source_count_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_box_count_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_amount_avg_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_amount_min_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_amount_max_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_source_count_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_box_count_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_amount_avg_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_amount_min_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    purchase_amount_max_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_customer_count_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_box_count_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_amount_avg_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_amount_min_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_amount_max_14d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_customer_count_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_box_count_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_amount_avg_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_amount_min_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    sale_amount_max_30d = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # E-commerce currentorderable stock
    orderable_stock = models.FloatField(default=0.00)
    # E-commerce current stock
    ecom_stock = models.FloatField(default=0.00)
    issue_number = models.IntegerField(default=0)
    last_publish = models.DateTimeField(
        blank=True,
        null=True,
    )
    last_unpublish = models.DateTimeField(
        blank=True,
        null=True,
    )
    is_ad_enabled = models.BooleanField(default=False)


    class Meta:
        indexes = [
            models.Index(fields=['product',]),
            models.Index(fields=['status', 'is_salesable', 'store_point', 'stock', 'is_service', 'organization', 'product_full_name']),
            models.Index(fields=['product_len', '-local_count', '-organizationwise_count', '-global_count', 'product_full_name', 'id',]),
            models.Index(fields=['-local_count', '-organizationwise_count', '-global_count', 'product_len', 'product_full_name', 'id', ]),
            models.Index(fields=['-local_count', '-organizationwise_count', '-global_count', 'id',]),
        ]

        ordering = ('-local_count', '-organizationwise_count', '-global_count', 'id',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: #STORE: {} - #PRODUCT: {}".format(self.id, self.store_point_id, self.product_id)

    def get_stock_by_store_and_product(self, store, product):
        try:
            return Stock.objects.get(
                store_point=store,
                product=product,
                status=Status.ACTIVE
            )
        except Stock.DoesNotExist:
            return None

    def get_queryset_for_cache(
        self,
        list_of_pks=None,
        request=None,
        is_distributor_stock=False):
        '''
        This method take a list of primary key of stocks and return queryset to cache them
        Parameters
        ----------
        self : pharmacy.model.Stock
            An instance of pharmacy.model.Stock model
        list_of_pks : list
            list of primary key of stocks it can be None of empty list
        Raises
        ------
        No error is raised by this method
        Returns
        -------
        queryset
            This method return queryset for given stock instance's pk
        '''

        from .helpers import add_sales_purchase_log_price
        # search keyword
        keyword = request.GET.get('keyword', '')
        # check any letter in keyword is in uppercase
        is_exact_search = True if any(map(str.isupper, str(keyword))) else False
        if list_of_pks is None or len(list_of_pks) == 0:
            list_of_pks = [self.id,]

        queryset = Stock.objects.filter(
            id__in=list_of_pks
        ).select_related(
            'store_point',
            'product',
            'product__manufacturing_company',
            'product__subgroup',
            'product__subgroup__product_group',
            'product__form',
            'product__generic',
            'product__primary_unit',
            'product__secondary_unit',
            'product__category',
            'latest_purchase_unit',
            'latest_sale_unit',
        ).only(
            'id',
            'alias',
            'stock',
            'orderable_stock',
            'demand',
            'auto_adjustment',
            'minimum_stock',
            'rack',
            'tracked',
            'sales_rate',
            'purchase_rate',
            'calculated_price',
            'order_rate',
            'discount_margin',
            'store_point__id',
            'store_point__alias',
            'store_point__name',
            'store_point__phone',
            'store_point__address',
            'store_point__type',
            'store_point__populate_global_product',
            'store_point__auto_adjustment',
            'store_point__created_at',
            'store_point__updated_at',
            'product__id',
            'product__code',
            'product__species',
            'product__alias',
            'product__name',
            'product__strength',
            'product__full_name',
            'product__description',
            'product__trading_price',
            'product__purchase_price',
            'product__status',
            'product__is_salesable',
            'product__is_service',
            'product__is_global',
            'product__conversion_factor',
            'product__category',
            'product__is_printable',
            'product__image',
            'product__order_limit_per_day',
            'product__is_queueing_item',
            'product__discount_rate',
            'product__order_mode',

                'product__manufacturing_company__id',
                'product__manufacturing_company__alias',
                'product__manufacturing_company__name',
                'product__manufacturing_company__description',
                'product__manufacturing_company__is_global',

                'product__form__id',
                'product__form__alias',
                'product__form__name',
                'product__form__description',
                'product__form__is_global',

                'product__subgroup__id',
                'product__subgroup__alias',
                'product__subgroup__name',
                'product__subgroup__description',
                'product__subgroup__is_global',

                    'product__subgroup__product_group__id',
                    'product__subgroup__product_group__alias',
                    'product__subgroup__product_group__name',
                    'product__subgroup__product_group__description',
                    'product__subgroup__product_group__is_global',
                    'product__subgroup__product_group__type',

                'product__generic__id',
                'product__generic__alias',
                'product__generic__name',
                'product__generic__description',
                'product__generic__is_global',

                'product__category__id',
                'product__category__alias',
                'product__category__name',
                'product__category__description',
                'product__category__is_global',

                'product__primary_unit__id',
                'product__primary_unit__alias',
                'product__primary_unit__name',
                'product__primary_unit__description',

                'product__secondary_unit__id',
                'product__secondary_unit__alias',
                'product__secondary_unit__name',
                'product__secondary_unit__description',

            'latest_purchase_unit__id',
            'latest_purchase_unit__alias',
            'latest_purchase_unit__name',
            'latest_purchase_unit__description',
            'latest_purchase_unit__created_at',
            'latest_purchase_unit__updated_at',

            'latest_sale_unit__id',
            'latest_sale_unit__alias',
            'latest_sale_unit__name',
            'latest_sale_unit__description',
            'latest_sale_unit__created_at',
            'latest_sale_unit__updated_at',
        )
        # If request for distributor stock return queryset without modification
        if is_distributor_stock:
            return queryset
        queryset = add_sales_purchase_log_price(queryset)
        if request is not None:
            if is_exact_search:
                queryset = queryset.order_by(
                    'product_len', '-local_count', '-organizationwise_count',
                    '-global_count', 'product_full_name', 'id'
                )

            elif keyword:
                queryset = queryset.order_by(
                    '-local_count', '-organizationwise_count', '-global_count',
                    'product_len', 'product_full_name', 'id'
                )

            else:
                queryset = queryset.order_by(
                    '-local_count', '-organizationwise_count',
                    '-global_count', 'id'
                )
        return queryset

    def get_batch_info(self):

        raw_query = '''
        SELECT * FROM (
        SELECT stock_id                              AS id,
            stock_id,
            batch,
            Min(expire_date) as expire_date,
            Sum(stock_in) - Sum(stock_out) AS quantity
        FROM   (SELECT stock_id,
                    batch,
                    Min(expire_date) AS expire_date,
                    Sum(quantity)    AS stock_in,
                    0                AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  stock_id = {0}
                    AND type = 0
                    AND sio.status = 0
                GROUP  BY stock_id,
                        batch
                UNION
                SELECT stock_id,
                    batch,
                    '2099-12-12'  AS expire_date,
                    0             AS stock_in,
                    Sum(quantity) AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  stock_id = {0}
                    AND type = 1
                    AND sio.status = 0
                GROUP  BY stock_id,
                        batch) AS a
        GROUP  BY stock_id,
                batch
        ) as data WHERE quantity > 0'''
        raw_query = raw_query.format(self.id)

        return StockIOLog.objects.raw(raw_query)

    def get_quantity_from_io(self):
        """[summary]
        get stock quantity calculating io logs
        Returns:
            [Float] -- [the stock quantity]
        """
        io_logs = StockIOLog.objects.filter(
            Q(purchase__isnull=True) | Q(
                purchase__purchase_type=PurchaseType.PURCHASE),
            status=Status.ACTIVE,
            stock=self,
        ).values(
            'stock'
        ).order_by('stock').annotate(
            total_qty=Coalesce(Sum(Case(When(type=StockIOType.INPUT, then=F('quantity')))), 0.00) -
            Coalesce(
                Sum(Case(When(type=StockIOType.OUT, then=F('quantity')))), 0.00),
        )
        return io_logs.first()['total_qty'] if io_logs else 0.00

    def expire_cache(self):
        # cache_expire.apply_async(
        #     ('stock_instance_{}'.format(str(self.id).zfill(12)),),
        #     countdown=5,
        #     retry=True, retry_policy={
        #         'max_retries': 10,
        #         'interval_start': 0,
        #         'interval_step': 0.2,
        #         'interval_max': 0.2,
        #     }
        # )
        stock_key_list = [
            "stock_instance_{}".format(str(self.id).zfill(12)),
            f"{STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX}_{str(self.id).zfill(12)}"
        ]

        cache_expire_list.apply_async(
            (stock_key_list, ),
            countdown=5,
            retry=True, retry_policy={
                "max_retries": 10,
                "interval_start": 0,
                "interval_step": 0.2,
                "interval_max": 0.2,
            }
        )

    def update_avg_purchase_rate(self):
        """[summary]
            This method will fetch last three purchase and update the avg_purchase rate
        Returns:
            [type]: [description]
        """
        last_three_purchase = self.stocks_io.filter(
            status=Status.ACTIVE,
            purchase__isnull=False,
            purchase__is_sales_return=False
        ).values_list('pk', flat=True).order_by('-pk')[:3]
        if last_three_purchase:
            io = StockIOLog.objects.filter(
                pk__in=Subquery(last_three_purchase)
            ).aggregate(
                avg_purchase_rate=Coalesce(Sum(Case(
                    When(secondary_unit_flag=True, then=(
                        (F('rate') / F('conversion_factor')
                         ) * F('quantity')) - F('discount_total') + F('vat_total') + F('round_discount')),
                    When(secondary_unit_flag=False, then=(
                        (F('quantity') * F('rate')) - F('discount_total') + F('vat_total') + F('round_discount'))),
                    output_field=FloatField(),
                )), 0.00) / Coalesce(Sum(F('quantity')), 0.00),
            )
            self.avg_purchase_rate = round(io.get('avg_purchase_rate', 0), 2)
            self.save(update_fields=['avg_purchase_rate'])


    @property
    def avg_daily_order_quantity(self):

        days_count = [1, 7, 15, 30]
        days_label = ['24 hours', '7 days', '15 days', '30 days']

        order = Purchase.objects.filter(
            distributor__id=41,
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).exclude(
            current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
        )

        result = {}
        for i in range(len(days_count)):
            data = StockIOLog.objects.filter(
                stock=self,
                purchase__in=order.filter(created_at__gte=datetime.now(DTTZ.utc)-timedelta(days=days_count[i]))
            )
            _sum = 0
            if data.exists():
                _sum = data.aggregate(Sum('quantity'))['quantity__sum']/days_count[i]
            result.update( {days_label[i] : "{:.2f}".format(_sum)})
        return result

    @property
    def avg_daily_order_count(self):

        days_count = [1, 7, 15, 30]
        days_label = ['24 hours', '7 days', '15 days', '30 days']

        order = Purchase.objects.filter(
            distributor__id=303,
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).exclude(
            current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED ]
        )

        result = {}
        for i in range(len(days_count)):
            data = StockIOLog.objects.filter(
                stock=self,
                purchase__in=order.filter(created_at__gte=datetime.now(DTTZ.utc)-timedelta(days=days_count[i]))
            )
            _sum = 0
            if data.exists():
                _sum = data.aggregate(purchase__count=Count('purchase'))['purchase__count']/days_count[i]
            result.update( {days_label[i] : "{:.2f}".format(_sum)})
        return result

    @property
    def avg_daily_discount(self):

        days_count = [1, 7, 15, 30]
        days_label = ['24 hours', '7 days', '15 days', '30 days']

        order = Purchase.objects.filter(
            distributor__id=303,
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).exclude(
            current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED ]
        )

        result = {}
        for i in range(len(days_count)):
            data = StockIOLog.objects.filter(
                stock=self,
                purchase__in=order.filter(created_at__gte=datetime.now(DTTZ.utc)-timedelta(days=days_count[i]))
            )
            _avg = 0
            if data.exists():
                _avg = data.aggregate(discount_rate__avg=Avg('discount_rate'))['discount_rate__avg']
            result.update( {days_label[i] : "{:.2f}".format(_avg)})
        return result

    def get_avg_purchase_rate_by_days(self, days=0):
        from django.utils import timezone
        end_date = str(date.today())
        start_date = str(date.today() + relativedelta(days=-(days)))
        start_date = datetime.combine(
            datetime.strptime(start_date, '%Y-%m-%d'), time.min)
        end_date = str(date.today())
        end_date = datetime.combine(
            datetime.strptime(end_date, '%Y-%m-%d'), time.max)
        start_date = timezone.make_aware(
            start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(
            end_date, timezone.get_current_timezone())
        io_logs = self.stocks_io.filter(
            status=Status.ACTIVE,
            purchase__isnull=False,
            purchase__purchase_type=PurchaseType.PURCHASE,
            purchase__status=Status.ACTIVE,
            purchase__purchase_date__range=[start_date, end_date]
        )
        io_logs = io_logs.aggregate(
            avg_purchase_rate=Coalesce(Sum(Case(
                When(secondary_unit_flag=True, then=(
                    (F('rate') / F('conversion_factor')
                    ) * F('quantity')) - F('discount_total') + F('vat_total') + F('round_discount')),
                When(secondary_unit_flag=False, then=(
                    (F('quantity') * F('rate')) - F('discount_total') + F('vat_total') + F('round_discount'))),
                output_field=FloatField(),
            )), 0.00) / Sum(F('quantity')),
        )
        avg_purchase_rate = io_logs.get('avg_purchase_rate', None)
        return round(avg_purchase_rate, 3) if avg_purchase_rate else avg_purchase_rate

    @property
    def avg_purchase_rate_days(self):
        return {
            "today": self.get_avg_purchase_rate_by_days(),
            "yesterday": self.get_avg_purchase_rate_by_days(1),
            "last_3_days": self.get_avg_purchase_rate_by_days(3),
            "last_7_days": self.get_avg_purchase_rate_by_days(7),
            "last_15_days": self.get_avg_purchase_rate_by_days(15),
            "last_30_days": self.get_avg_purchase_rate_by_days(30),
        }

    @property
    def avg_purchase_rate_today(self):
        return self.get_avg_purchase_rate_by_days()

    @property
    def avg_purchase_rate_yesterday(self):
        return self.get_avg_purchase_rate_by_days(1)

    @property
    def avg_purchase_rate_last_3_days(self):
        return self.get_avg_purchase_rate_by_days(3)

    @property
    def avg_purchase_rate_last_7_days(self):
        return self.get_avg_purchase_rate_by_days(7)

    @property
    def avg_purchase_rate_last_15_days(self):
        return self.get_avg_purchase_rate_by_days(15)

    @property
    def avg_purchase_rate_last_30_days(self):
        return self.get_avg_purchase_rate_by_days(30)

    def get_current_orderable_stock(self, current_stock = None):
        io_logs = self.stocks_io.filter(
            ((Q(purchase__current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.READY_TO_DELIVER,
            ]) &
            Q(purchase__is_delayed=False)) |
            (Q(purchase__is_delayed=True) &
            Q(purchase__current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.READY_TO_DELIVER,
            ]))),
            status=Status.DISTRIBUTOR_ORDER,
            purchase__status=Status.DISTRIBUTOR_ORDER,
            purchase__distributor_order_type=DistributorOrderType.ORDER,
            purchase__purchase_type=PurchaseType.VENDOR_ORDER,
            # purchase__current_order_status__in=[
            #     OrderTrackingStatus.PENDING,
            #     OrderTrackingStatus.ACCEPTED,
            #     OrderTrackingStatus.READY_TO_DELIVER,
            # ]
        ).only("quantity").aggregate(total_qty=Coalesce(Sum(F('quantity')), 0.00))
        if current_stock is not None:
            return current_stock - io_logs.get('total_qty')
        return self.ecom_stock - io_logs.get('total_qty')

    @property
    def current_orderable_stock(self, current_stock = None):
        return self.get_current_orderable_stock()

    def update_orderable_stock(self):
        self.orderable_stock = self.current_orderable_stock
        self.save(update_fields=['orderable_stock'])

    def get_last_stock_info_from_file(self):
        from core.models import ScriptFileStorage

        last_stock = 0
        file_upload_date = None
        files = ScriptFileStorage.objects.filter(
            status=Status.ACTIVE,
            file_purpose=FilePurposes.DISTRIBUTOR_STOCK,
            set_stock_from_file=True
        ).only('created_at', 'content').order_by('-pk')

        if files.exists():
            last_instance = files.first()
            stock_df =  pd.read_csv(last_instance.content)
            item_in_file = stock_df.loc[stock_df['ID'] == int(self.id)].to_dict(orient='records')
            last_stock = item_in_file[0].get('STOCK', 0) if item_in_file else 0
            file_upload_date = last_instance.created_at
            current_tz = django_timezone.get_current_timezone()
            to_local = file_upload_date.astimezone(current_tz)
        return {
            "stock": float(last_stock) if checkers.is_numeric(last_stock) else 0,
            "file_upload_date": str(to_local)
        }

    # Get current stock for e-commerce calculations all logs
    def get_calculated_stock_for_ecommerce(self):
        from core.models import ScriptFileStorage
        from ecommerce.models import ShortReturnItem

        stock_info = self.get_last_stock_info_from_file()
        file_upload_date = stock_info.get('file_upload_date')
        last_stock = stock_info.get('stock', 0)

        requisition_filters = {
            'status': Status.DRAFT,
            'purchase__purchase_date__gt': file_upload_date,
            'purchase__status': Status.DRAFT,
            'purchase__purchase_type': PurchaseType.REQUISITION
        }

        requisitions = self.stocks_io.filter(
            **requisition_filters
        ).aggregate(
            total_quantity=Coalesce(Sum(
                'quantity',
                output_field=FloatField()
            ), 0.00)
        )

        order_filters = {
            'status': Status.DISTRIBUTOR_ORDER,
            'purchase__order_status__date__gt': file_upload_date,
            'purchase__order_status__order_status': OrderTrackingStatus.ON_THE_WAY,
            'purchase__status': Status.DISTRIBUTOR_ORDER,
            'purchase__purchase_type': PurchaseType.VENDOR_ORDER,
            'purchase__distributor_order_type': DistributorOrderType.ORDER,
            'purchase__current_order_status__in': [
                OrderTrackingStatus.ON_THE_WAY,
                OrderTrackingStatus.DELIVERED,
                OrderTrackingStatus.COMPLETED,
                OrderTrackingStatus.PARITAL_DELIVERED,
                OrderTrackingStatus.FULL_RETURNED,
                OrderTrackingStatus.PORTER_DELIVERED,
                OrderTrackingStatus.PORTER_FULL_RETURN,
                OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
                OrderTrackingStatus.PORTER_FAILED_DELIVERED,
            ]
        }
        orders = self.stocks_io.filter(
            **order_filters
        ).aggregate(
            total_quantity=Coalesce(Sum(
                'quantity',
                output_field=FloatField()
            ), 0.00),
        )

        short_return_filters = {
            'short_return_log__date__gt': file_upload_date,
        }
        short_return_items = self.stocks_short_return.filter(
            **short_return_filters
        ).exclude(
            status=Status.INACTIVE,
        ).exclude(
            short_return_log__invoice_group__current_order_status__in=[
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED
            ]
        ).aggregate(
            total_quantity = Coalesce(
                Sum(
                    'quantity',
                    output_field=FloatField()
                ), 0.00
            )
        )

        current_stock = last_stock + requisitions.get('total_quantity', 0) + float(short_return_items.get('total_quantity', 0)) - orders.get('total_quantity', 0)
        return current_stock

    def get_stock_change_history(self):
        stock_info = self.get_last_stock_info_from_file()
        file_upload_date = stock_info.get('file_upload_date')

        requisition_filters = {
            'status': Status.DRAFT,
            'purchase__purchase_date__gt': file_upload_date,
            'purchase__status': Status.DRAFT,
            'purchase__purchase_type': PurchaseType.REQUISITION
        }

        requisitions = self.stocks_io.filter(
            **requisition_filters
        ).values(
            'date',
        ).annotate(
            total_quantity=Coalesce(Sum(
                'quantity',
                output_field=FloatField()
            ), 0.00)
        ).order_by()

        order_filters = {
            'status': Status.DISTRIBUTOR_ORDER,
            'purchase__order_status__date__gt': file_upload_date,
            'purchase__order_status__order_status': OrderTrackingStatus.ON_THE_WAY,
            'purchase__status': Status.DISTRIBUTOR_ORDER,
            'purchase__purchase_type': PurchaseType.VENDOR_ORDER,
            'purchase__distributor_order_type': DistributorOrderType.ORDER,
            'purchase__current_order_status__in': [
                OrderTrackingStatus.ON_THE_WAY,
                OrderTrackingStatus.DELIVERED,
                OrderTrackingStatus.COMPLETED,
                OrderTrackingStatus.PARITAL_DELIVERED,
                OrderTrackingStatus.FULL_RETURNED,
                OrderTrackingStatus.PORTER_DELIVERED,
                OrderTrackingStatus.PORTER_FULL_RETURN,
                OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
                OrderTrackingStatus.PORTER_FAILED_DELIVERED,
            ]
        }
        orders = self.stocks_io.filter(
            **order_filters
        ).values(
            'purchase__tentative_delivery_date',
        ).annotate(
            total_quantity=Coalesce(Sum(
                'quantity',
                output_field=FloatField()
            ), 0.00),
        ).order_by()

        short_filters = {
            'short_return_log__approved_at__gt': file_upload_date,
            'type': ShortReturnLogType.SHORT
        }
        short_items = self.stocks_short_return.filter(
            **short_filters
        ).exclude(
            status=Status.INACTIVE,
        ).exclude(
            short_return_log__invoice_group__current_order_status__in=[
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED
            ]
        ).values(
            'date',
        ).order_by().annotate(
            total_quantity = Coalesce(
                Sum(
                    'quantity',
                    output_field=FloatField()
                ), 0.00
            )
        )

        return_filters = {
            'short_return_log__approved_at__gt': file_upload_date,
            'type': ShortReturnLogType.RETURN
        }
        return_items = self.stocks_short_return.filter(
            **return_filters
        ).exclude(
            status=Status.INACTIVE,
        ).exclude(
            short_return_log__invoice_group__current_order_status__in=[
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED
            ]
        ).values(
            'date',
        ).order_by().annotate(
            total_quantity = Coalesce(
                Sum(
                    'quantity',
                    output_field=FloatField()
                ), 0.00
            )
        )

        return {
            'info_stock_from_file': stock_info,
            'requisitions': requisitions,
            'orders_out_for_delivery': orders,
            'shorts': short_items,
            'returns': return_items,
            'current_stock': self.ecom_stock,
            'calculated_stock': self.get_calculated_stock_for_ecommerce()
        }

    @property
    def is_limited_stock(self):
        from common.healthos_helpers import HealthOSHelper
        healthos_helper = HealthOSHelper()
        try:
            healthos_settings = healthos_helper.settings()
            if healthos_settings.overwrite_order_mode_by_product:
                product = Product.objects.only('order_mode').get(pk=self.product_id)
                return product.order_mode == AllowOrderFrom.STOCK
            return healthos_settings.allow_order_from == AllowOrderFrom.STOCK
        except:
            return False

    @property
    def is_trending(self):
        from common.healthos_helpers import HealthOSHelper

        healthos_helper = HealthOSHelper()
        trending_items_pk_list = healthos_helper.get_trending_products_pk_list()
        return self.id in trending_items_pk_list

    def get_product_order_mode(self):
        from common.utils import get_healthos_settings

        try:
            setting = get_healthos_settings()
            if setting.overwrite_order_mode_by_product:
                product = Product.objects.only("order_mode").get(pk=self.product_id)
                product_order_mode = product.order_mode
            else:
                product_order_mode = setting.allow_order_from
                # if order mood is stock and open then product order mode will be the order mode.
                if setting.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN:
                    product = Product.objects.only("order_mode").get(pk=self.product_id)
                    product_order_mode = product.order_mode
            return product_order_mode
        except:
            return 0

    @property
    def product_order_mode(self):
        return self.get_product_order_mode()

    @property
    def is_out_of_stock(self):
        from common.utils import get_healthos_settings
        # Stock_and_Open:
        # 1. if order mode is Stock_and_Open then we consider product order mode as the order mode
        # 2. if product order_mode is Stock_and_Next_day then we need to return False unless product
        #    has orderable quantity greater then 0 the we need to return True
        order_mode = self.get_product_order_mode()
        # we are getting updated order mode of the product from get_product_order_mode
        # if order mode is by Organization and its Stock_and_Open
        setting = get_healthos_settings()
        if (
            order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
            self.orderable_stock <= 0 and
            setting.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN and
            not setting.overwrite_order_mode_by_product
        ):
            order_mode = AllowOrderFrom.STOCK

        # IF stock is 0 and product__order_mode is STOCK, then is_out_of_stock is True, otherwise False
        return self.orderable_stock <= 0 and order_mode == AllowOrderFrom.STOCK

    def get_organization_order_reopening_time(self):
        from .utils import get_tentative_delivery_date

        distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        try:
            setting = Organization.objects.get(pk=distributor_id).get_settings()
            order_re_opening_date = setting.order_re_opening_date
            if order_re_opening_date:
                order_re_opening_date = get_tentative_delivery_date(
                    order_re_opening_date,
                )
                return order_re_opening_date
            return None
        except:
            return None

    @property
    def delivery_date(self):
        from .utils import get_delivery_date_for_product

        return get_delivery_date_for_product(self.product.is_queueing_item)

    @property
    def is_order_enabled(self):
        from .utils import get_organization_order_closing_and_reopening_time
        order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time()

        return not order_closing_date and not order_reopening_date

    @property
    def is_delivery_coupon(self):
        from common.healthos_helpers import HealthOSHelper

        healthos_helper = HealthOSHelper()
        return self.id == healthos_helper.get_delivery_coupon_stock_id()


class StockIOLog(CreatedAtUpdatedAtBaseModelWithOrganization):
    stock = models.ForeignKey(
        Stock,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='stocks_io'
    )
    quantity = models.FloatField(default=0.00)
    rate = models.FloatField(default=0.00)
    batch = models.CharField(max_length=128)
    expire_date = models.DateField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    type = fields.SelectIntegerField(blueprint=StockIOType)
    sales = models.ForeignKey(
        'Sales',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='stock_io_logs'
    )
    purchase = models.ForeignKey(
        'Purchase',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='stock_io_logs'
    )
    transfer = models.ForeignKey(
        'StockTransfer',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='stock_io_logs'
    )
    adjustment = models.ForeignKey(
        'StockAdjustment',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='stock_io_logs'
    )
    # patient = models.ForeignKey(
    #     Person,
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     related_name='stock_io_patient'
    # )

    # person_organization_patient = models.ForeignKey(
    #     PersonOrganization, models.DO_NOTHING,
    #     related_name='stock_io_log_patient_person_organization',
    #     blank=True,
    #     null=True,
    #     verbose_name=('io log paitent in person organization'),
    #     db_index=True
    # )
    primary_unit = models.ForeignKey(
        Unit,
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='stock_io_primary_unit'
    )
    secondary_unit = models.ForeignKey(
        Unit,
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='stock_io_secondary_unit'
    )
    discount_rate = models.FloatField(default=0.00)
    discount_total = models.FloatField(default=0.00)
    vat_rate = models.FloatField(default=0.00)
    vat_total = models.FloatField(default=0.00)
    tax_rate = models.FloatField(default=0.00)
    tax_total = models.FloatField(default=0.00)
    conversion_factor = models.FloatField(
        validators=[positive_non_zero],
        default=1.00
    )
    secondary_unit_flag = models.BooleanField(default=False)
    calculated_price = models.FloatField(
        default=0.00, help_text="Rate of individual product stockpoint-wise after calculating vat, tax, discount"
    )
    calculated_price_organization_wise = models.FloatField(
        default=0.00, help_text="Rate of individual product organization-wise after calculating vat, tax, discount"
    )
    round_discount = models.FloatField(
        default=0.00,
        help_text="discount amount distributed by inventory's round_discount"
    )
    data_entry_status = fields.SelectIntegerField(
        blueprint=DataEntryStatus,
        default=DataEntryStatus.DONE
    )
    # Ecom related fields
    calculated_profit = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    profit_data = JSONTextField(blank=True, null=True, default='{}')
    base_discount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="The discount rate from product before adding dynamic discount"
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.created_at, self.stock)

    @property
    def product_name(self):
        from .helpers import get_product_short_name
        return get_product_short_name(self.stock.product)

    def get_trade_price(self):
        if self.secondary_unit_flag:
            if self.conversion_factor != 0:
                return self.rate / self.conversion_factor
            return 0
        else:
            return self.rate

    def get_purchase_information(self):
        if self.purchase is None:
            return None
        else:
            info = {}
            info.update(
                {
                    "purchase": self.purchase,
                    "subtotal": self.purchase.amount - self.purchase.tax_total,
                    "discount": self.purchase.discount + self.purchase.round_discount,
                    "vat": self.purchase.vat_total,
                    "tax": self.purchase.tax_total,
                    "transport": self.purchase.transport,
                }
            )
            return info

    def get_purchase_price_info(self, storepoint_wise=True):
        '''
        This function return subtotal of relate purchase along with additional
        price to be distributed
        '''
        if storepoint_wise:
            purchase_info = self.get_purchase_information()
            # stock io belngs to purchase
            if purchase_info is not None:

                purchase_productwise_vat_tax = \
                    purchase_info['purchase'].stock_io_logs.filter(
                        status=Status.ACTIVE
                    ).aggregate(
                        sum_total_discount=Coalesce(Sum('discount_total'), 0.00),
                        sum_total_vat=Coalesce(Sum('vat_total'), 0.00),
                        sum_total_tax=Coalesce(Sum('tax_total'), 0.00)
                    )

                discount_to_be_dristributed = purchase_info['discount'] - \
                    purchase_productwise_vat_tax['sum_total_discount']
                vat_to_be_dristributed = purchase_info['vat'] - \
                    purchase_productwise_vat_tax['sum_total_vat']
                tax_to_be_dristributed = purchase_info['tax'] - \
                    purchase_productwise_vat_tax['sum_total_tax']
                transport_to_be_dristributed = purchase_info['transport']

                distributed_total_amount = \
                    vat_to_be_dristributed + tax_to_be_dristributed +\
                    transport_to_be_dristributed - discount_to_be_dristributed
                return purchase_info['subtotal'], distributed_total_amount
            # stock io does not belngs to purchase
            return None, None
        return None, None

    def replace_stock_in_stock_io(self, to_be_replaced, replace_with):
        StockIOLog.objects.filter(
            stock=to_be_replaced
        ).update(stock=replace_with)


class Sales(CreatedAtUpdatedAtBaseModelWithOrganization):
    sale_date = models.DateTimeField(blank=True, null=True)
    buyer = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='buyer',
        db_index=True
    )

    person_organization_buyer = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='buyer_patient_person_organization',
        blank=True,
        null=True,
        verbose_name=('buyer in person organization'),
        db_index=True
    )

    buyer_balance = models.FloatField(default=0.00)
    amount = models.FloatField(default=0.00)
    discount = models.FloatField(default=0.00)
    discount_rate = models.FloatField(default=0.00)
    transport = models.FloatField(default=0.00)
    # vat_rate for this purchase
    vat_rate = models.FloatField(default=0.00)
    # total vat for this sales
    vat_total = models.FloatField(default=0.00)
    # round discount of a sale
    round_discount = models.FloatField(default=0.00)
    salesman = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='salesman',
        db_index=True
    )

    person_organization_salesman = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='salesman_patient_person_organization',
        blank=True,
        null=True,
        verbose_name=('salesman in person organization'),
        db_index=True
    )

    gave = models.FloatField(null=True)
    sales_type = fields.SelectIntegerField(
        blueprint=SalesType, default=SalesType.RETAIL_CREDIT)
    sales_mode = fields.SelectIntegerField(
        blueprint=SalesModeType, default=SalesModeType.ONLINE,
        help_text=_('Sales is Online or Offline'))
    remarks = models.CharField(max_length=128, blank=True, null=True)
    transaction = models.ForeignKey(
        'account.Transaction', models.DO_NOTHING, blank=True, null=True,
        default=None, related_name='cash_sales_transaction')
    transactions = models.ManyToManyField(
        "account.Transaction", through='account.SalesTransaction',
        related_name='sales_tagged_transactions'
    )
    copied_from = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        db_index=True
    )
    patient_admission = models.ForeignKey(
        'clinic.PatientAdmission',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='sales_patient_admission',
        db_index=True
    )
    prescription = models.ForeignKey(
        'prescription.Prescription',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='sales_prescription',
        db_index=True
    )
    vouchar_no = models.CharField(
        max_length=32, blank=True, null=True, default=None)
    store_point = models.ForeignKey(
        StorePoint,
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='sales_on_storepoint',
        db_index=True)
    bill = models.ForeignKey(
        'account.PatientBill',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='sales_on_patient_bill',
        db_index=True
    )
    paid_amount = models.FloatField(default=0.00)
    is_purchase_return = models.BooleanField(default=False)
    organization_department = models.ForeignKey(
        'clinic.OrganizationDepartment',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='sales',
        db_index=True
    )
    editable = models.BooleanField(default=False)
    inactive_from = fields.SelectIntegerField(
        blueprint=SalesInactiveType, default=SalesInactiveType.FROM_ACTIVE,
        help_text=_('Determine inactive sales which is from ACTIVE or ON_HOLD or EDIT')
    )
    vat_tax_status = fields.SelectIntegerField(
        blueprint=VatTaxStatus,
        default=VatTaxStatus.DEFAULT,
        help_text=_('What types of vat, tax, discount was selected during sales')
    )
    # This field will use to store org of order placed organization
    buyer_organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='buyer_sales'
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "Sales"
        indexes = [
            models.Index(fields=['organization', 'status', 'is_purchase_return',]),
        ]

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.sale_date, self.buyer)

    def get_store_point_of_stock(self):
        if self.stock_io_logs.first():
            store_point = self.stock_io_logs.first().stock.store_point
            return store_point
        return None

    def get_sales_amount(self):
        sales_amount = self.amount + self.transport + self.round_discount
        if self.vat_rate > 0:
            sales_amount += ((self.amount / 100) * self.vat_rate)
        else:
            sales_amount += self.vat_total
        sales_amount -= self.discount
        return sales_amount

    def get_queryset_for_cache(self, list_of_pks=None, request=None):
        '''
        This method take a list of primary key of Sales and return queryset to cache them
        Parameters
        ----------
        self : pharmacy.model.Sales
            An instance of pharmacy.model.Sales model
        list_of_pks : list
            list of primary key of Sales it can be None of empty list
        Raises
        ------
        No error is raised by this method
        Returns
        -------
        queryset
            This method return queryset for given Sales instance's pk
        '''
        if list_of_pks is None or len(list_of_pks) == 0:
            list_of_pks = [self.id]

        queryset = Sales.objects.filter(
            pk__in=list_of_pks
        ).select_related(
            'store_point',
            'person_organization_buyer__person',
            'person_organization_salesman',
            'person_organization_salesman__designation',
            'person_organization_salesman__designation__department',
            'organization_department'
        ).only(
            'id',
            'alias',
            'status',
            'vouchar_no',
            'sale_date',
            'store_point',
                'store_point',
                'store_point__id',
                'store_point__alias',
                'store_point__created_at',
                'store_point__updated_at',
                'store_point__name',
                'store_point__phone',
                'store_point__address',
                'store_point__type',
                'store_point__populate_global_product',
                'store_point__auto_adjustment',
            'amount',
            'discount',
            'round_discount',
            'paid_amount',
            'transaction',
            'vat_total',
            'vouchar_no',
            'copied_from',
            'editable',
            'organization_wise_serial',
            'person_organization_buyer__person',
            'person_organization_buyer',
                'person_organization_buyer__id',
                'person_organization_buyer__alias',
                'person_organization_buyer__first_name',
                'person_organization_buyer__last_name',
                'person_organization_buyer__phone',
                'person_organization_buyer__person_group',
                'person_organization_buyer__code',
                'person_organization_buyer__dob',
                'person_organization_buyer__gender',
                # 'person_organization_buyer__economic_status',
                'person_organization_buyer__balance',
                # 'person_organization_buyer__diagnosis_with',
            'person_organization_salesman',
                'person_organization_salesman__id',
                'person_organization_salesman__alias',
                'person_organization_salesman__first_name',
                'person_organization_salesman__last_name',
                'person_organization_salesman__phone',
                'person_organization_salesman__person_group',
                'person_organization_salesman__degree',
                'person_organization_salesman__code',
                'person_organization_salesman__designation',
                    'person_organization_salesman__designation__id',
                    'person_organization_salesman__designation__alias',
                    'person_organization_salesman__designation__name',
                    'person_organization_salesman__designation__description',
                    'person_organization_salesman__designation__department',
                            'person_organization_salesman__designation__department__id',
                            'person_organization_salesman__designation__department__alias',
                            'person_organization_salesman__designation__department__name',
                            'person_organization_salesman__designation__department__description',
            'organization_department',
                'organization_department__id',
                'organization_department__alias',
                'organization_department__name',
                'organization_department__description',
                'organization_department__is_global',
                'organization_department__status',
        ).order_by('-id')

        return queryset

class StockTransfer(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateField(blank=True, null=True)
    transfer_from = models.ForeignKey(
        StorePoint, models.DO_NOTHING, blank=False, null=False, related_name='store_from')
    transfer_to = models.ForeignKey(
        StorePoint, models.DO_NOTHING, blank=False, null=False, related_name='store_to')
    transport = models.FloatField(default=0.00)
    by = models.ForeignKey(Person, models.DO_NOTHING, blank=False,
                           null=False, related_name='stock_transfer_by')
    person_organization_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='transfer_by_person_organization',
        blank=True,
        null=True,
        verbose_name=('transfer by in person organization'),
        db_index=True
    )
    received_by = models.ForeignKey(Person, models.DO_NOTHING, blank=True,
                                    null=True, default=None, related_name='stock_transfer_received')

    person_organization_received_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='transfer_received_by_person_organization',
        blank=True,
        null=True,
        verbose_name=('transfer received by in person organization'),
        db_index=True
    )

    remarks = models.CharField(max_length=128, blank=True, null=True)
    transfer_status = fields.SelectIntegerField(
        blueprint=TransferStatusType, default=TransferStatusType.PROPOSED_TRANSFER)

    copied_from = models.ForeignKey(
        'self', models.DO_NOTHING, blank=True, null=True, default=None)
    requisitions = models.ManyToManyField(
        'self', through="pharmacy.PurchaseRequisition",
        related_name="stock_transfer_requisitions", symmetrical=False)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "Stock Transfer"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.date, self.transfer_from)


class Purchase(CreatedAtUpdatedAtBaseModelWithOrganization):
    purchase_type = fields.SelectIntegerField(
        blueprint=PurchaseType, default=PurchaseType.PURCHASE)
    purchase_order_status = fields.SelectIntegerField(
        blueprint=PurchaseOrderStatus, default=PurchaseOrderStatus.DEFAULT)
    purchase_date = models.DateTimeField(blank=True, null=True)
    requisition_date = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey(
        Person, models.DO_NOTHING, blank=True, null=True, default=None, related_name='supplier')

    person_organization_supplier = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='purchase_supplier_person_organization',
        blank=True,
        null=True,
        verbose_name=('supplier in person organization'),
        db_index=True
    )

    department = models.ForeignKey(
        Department, models.DO_NOTHING,
        blank=True, null=True, related_name='purchase_department')

    # subtotal amount : sum of products qty * product price
    amount = models.FloatField(default=0.00)
    # discount : discount without round amount
    discount = models.FloatField(default=0.00)
    # discount_rate: to trace is discount given by rate or amount
    # if given by amount then discount rate will be 0
    discount_rate = models.FloatField(default=0.00)
    # discount round : another form of discount
    round_discount = models.FloatField(default=0.00)
    vat_rate = models.FloatField(default=0.00)
    # total vat for this purchase
    vat_total = models.FloatField(default=0.00)
    tax_rate = models.FloatField(default=0.00)
    # total tax  for this purchase
    tax_total = models.FloatField(default=0.00)
    grand_total = models.FloatField(default=0.00)
    # total transport  for this purchase
    transport = models.FloatField(default=0.00)
    receiver = models.ForeignKey(
        Person, models.DO_NOTHING, blank=False, null=False, related_name='receiver')

    person_organization_receiver = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='purchase_receiver_person_organization',
        blank=True,
        null=True,
        verbose_name=('receiver in person organization'),
        db_index=True
    )

    remarks = models.CharField(max_length=512, blank=True, null=True)
    is_sales_return = models.BooleanField(default=False)

    copied_from = models.ForeignKey(
        'self', models.DO_NOTHING, blank=True, null=True, default=None, related_name="purchases")
    requisitions = models.ManyToManyField(
        'self', through="pharmacy.PurchaseRequisition",
        related_name="purchase_requisitions", symmetrical=False)
    sales_return = models.ManyToManyField(
        Sales, through="pharmacy.SalesReturn",
        related_name="sales_return_by_purchase"
    )
    patient_admission = models.ForeignKey(
        'clinic.PatientAdmission', models.DO_NOTHING, blank=True, null=True,
        related_name='purchase_patient_admission')
    vouchar_no = models.CharField(
        max_length=512, blank=True, null=True, default=None)
    store_point = models.ForeignKey(
        StorePoint,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='purchased_on_storepoint')
    purchase_payment = models.FloatField(default=0.00)
    organization_department = models.ForeignKey(
        'clinic.OrganizationDepartment',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='purchases',
        db_index=True
    )
    # Fields for vendor/distributor order start here
    distributor = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='orders',
        db_index=True,
        help_text='Vendor / Distributor organization'
    )
    distributor_order_group = models.ForeignKey(
        'pharmacy.DistributorOrderGroup',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='order_groups',
        db_index=True,
        help_text='Order group for distributor order'
    )
    distributor_order_type = fields.SelectIntegerField(
        blueprint=DistributorOrderType,
        default=DistributorOrderType.CART,
        help_text='Define cart or order'
    )
    invoice_group = models.ForeignKey(
        'ecommerce.OrderInvoiceGroup',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='orders',
        db_index=True,
        help_text='Order invoice group for distributor order'
    )
    current_order_status = fields.SelectIntegerField(
        blueprint=OrderTrackingStatus,
        default=OrderTrackingStatus.PENDING,
        help_text='Define current status of order'
    )
    system_platform = fields.SelectIntegerField(
        blueprint=SystemPlatforms,
        default=SystemPlatforms.WEB_APP,
        help_text='Define system playform web/android-app/ios-app'
    )
    sales = models.ForeignKey(
        Sales,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='orders',
        help_text='Sales for an order'
    )
    responsible_employee = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='distributor_orders',
        blank=True,
        null=True,
        verbose_name=('responsible person organization for orders'),
    )
    additional_discount = models.FloatField(default=0.00)
    additional_discount_rate = models.FloatField(default=0.00)
    additional_cost = models.FloatField(default=0.00)
    additional_cost_rate = models.FloatField(default=0.00)
    geo_location_data = JSONTextField(blank=True, null=True, default='{}')
    # Next Day flag for e-commerce
    is_queueing_order = models.BooleanField(
        default=False,
        help_text="Next day flag for e-commerce"
    )
    tentative_delivery_date = models.DateField(blank=True, null=True)
    # Ecom related fields
    calculated_profit = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    profit_data = JSONTextField(blank=True, null=True, default='{}')
    # Fields for vendor/distributor order ends here

    # rating fields
    order_rating = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    order_rating_comment = models.TextField(blank=True, null=True)
    is_delayed = models.BooleanField(default=False)
    calculated_profit = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    customer_dynamic_discount_factor = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="The dynamic discount of a customer org when the order is placed"
    )
    customer_area_dynamic_discount_factor = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="The dynamic discount of a customer's area when the order is placed"
    )
    dynamic_discount_amount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="The additional discount amount customer get for dynamic discount"
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "Purchases"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.purchase_date, self.supplier_id)

    # Return the current tracking status as property
    @property
    def current_status(self):
        tracking_instance = self.order_status.order_by('-pk').first()
        if tracking_instance:
            return tracking_instance.order_status
        return OrderTrackingStatus.PENDING

    @current_status.setter
    def current_status(self, value):
        if OrderTrackingStatus.is_in_values(value):
            order_tracking = OrderTracking.objects.get_or_create(
                order=self,
                order_status=value
            )
        else:
            raise ValueError('Invalid Choice')

    def get_store_point_of_stock(self):
        if self.stock_io_logs.first():
            store_point = self.stock_io_logs.first().stock.store_point
            return store_point
        return None

    # Get purchase order pending amounts
    def get_pending_amount(self):
        try:
            amount = Purchase.objects.filter(
                status=Status.ACTIVE,
                copied_from=self.pk
            ).values_list('grand_total', flat=True)
        except Purchase.DoesNotExist:
            return 0

        return self.grand_total - sum(amount)

    def get_transaction_purchase(self):
        return self.transaction_purchase.filter(status=Status.ACTIVE)

    # Return sub total and total discount calculating iolog items
    def get_amount(self):
        items = StockIOLog.objects.filter(
            purchase__id=self.id
        ).exclude(status=Status.INACTIVE).order_by()
        items = items.values('purchase').aggregate(
            sub_total=Coalesce(Round(Sum(Case(
                When(secondary_unit_flag=True, then=(
                    F('rate') / F('conversion_factor')
                ) * F('quantity')),
                When(secondary_unit_flag=False, then=(
                    F('quantity') * F('rate'))),
                output_field=FloatField(),
            ) + F('vat_total'))), 0.00),
            total_discount=Coalesce(Round(Sum(F('discount_total'))), 0.00),
            total_round_discount=Coalesce(Round(Sum(F('round_discount'))), 0.00)
        )
        return items

    def is_valid_tracking_status(self, tracking_status):
        tracking_statuses = self.order_status.filter(
            order_status=tracking_status
        )
        return False if tracking_statuses.exists() else True

    def create_stock_delivery_instance(self, delivery_instance_id):
        from delivery.models import StockDelivery
        io_logs = self.stock_io_logs.filter(
            status=Status.DISTRIBUTOR_ORDER
        )
        common_fields = [
            'quantity',
            'rate',
            'batch',
            'discount_rate',
            'discount_total',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'round_discount',
            'id',
            'status',
            'stock',
        ]

        for item in io_logs:
            data = item.to_dict(_fields=common_fields)
            data['stock_io_id'] = data.pop('id')
            data['stock_id'] = data.pop('stock')
            data['order_id'] = self.id
            data['organization_id'] = self.distributor_id
            data['product_name'] = item.product_name
            if item.secondary_unit_flag and item.secondary_unit_id:
                data['unit'] = item.secondary_unit_id.name
            elif item.primary_unit_id:
                data['unit'] = item.primary_unit.name
            else:
                data['unit'] = 'N/A'
            data['entry_by_id'] = self.updated_by_id
            data['delivery_id'] = delivery_instance_id
            data['date'] = item.date
            data['expire_date'] = item.expire_date
            stock_delivery = StockDelivery.objects.create(**data)
            stock_delivery.save()

    def create_delivery_instance(self):
        from delivery.enums import DeliveryTrackingStatus
        from delivery.models import OrderDeliveryConnector, Delivery
        order = self
        assigned_by = None
        if order.updated_by_id:
            assigned_by = order.updated_by.get_person_organization_for_employee()
        assigned_by_id = assigned_by.id if assigned_by else None
        delivery_instances = OrderDeliveryConnector.objects.filter(
            status=Status.ACTIVE,
            order=order
        )
        if delivery_instances.exists():
            return
        else:
            org_delivery_instance = Delivery.objects.filter(
                status=Status.ACTIVE,
                tracking_status=DeliveryTrackingStatus.READY_TO_DELIVER,
                order_by_organization_id=order.organization_id,
                assigned_to_id=order.responsible_employee_id
            )
            if org_delivery_instance.exists():
                order_delivery_connector = OrderDeliveryConnector.objects.create(
                    order=order,
                    delivery=org_delivery_instance.first(),
                    entry_by_id=order.updated_by_id
                )
                order_delivery_connector.save()
                order.create_stock_delivery_instance(org_delivery_instance.first().id)
            else:
                fields = [
                    'amount',
                    'discount',
                    'discount_rate',
                    'round_discount',
                    'vat_rate',
                    'vat_total',
                    'tax_rate',
                    'tax_total',
                    'grand_total'
                ]
                data = order.to_dict(_fields=fields)
                delivery_instance = Delivery.objects.create(
                    organization_id=order.distributor_id,
                    order_by_organization_id=order.organization_id,
                    assigned_by_id=assigned_by_id,
                    assigned_to_id=order.responsible_employee_id,
                    entry_by_id=order.updated_by_id,
                    **data
                )
                delivery_instance.save()
                order_delivery_connector = OrderDeliveryConnector.objects.create(
                    order=order,
                    delivery=delivery_instance
                )
                order_delivery_connector.save()
                order.create_stock_delivery_instance(delivery_instance.id)


    def clone_order(self, order_invoice_group_id = None, delivery_date=""):
        import time
        from .utils import get_tentative_delivery_date

        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
        DATE_FORMAT = '%Y-%m-%d'
        _datetime_now = datetime.strptime(
            time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
        _date_now = datetime.strptime(
            time.strftime(DATE_FORMAT, time.localtime()), DATE_FORMAT).date()
        ignore_fields = [
            'id',
            'alias',
            'purchase_date',
            'requisition_date',
            'supplier',
            'person_organization_supplier',
            'department',
            'remarks',
            'copied_from',
            'patient_admission',
            'vouchar_no',
            'purchase_payment',
            'organization_department',
            'sales',
            'requisitions',
            'sales_return',
            'distributor_order_group',
            'responsible_employee',
            'invoice_group',
        ]
        ignore_io_fields = [
            'id',
            'alias',
            'date',
            'sales',
            'transfer',
            'adjustment',
            'patient',
            'person_organization_patient',
            'purchase',
        ]
        fk_fields = [
            'entry_by',
            'updated_by',
            'organization',
            'receiver',
            'person_organization_receiver',
            'store_point',
            'distributor',
        ]
        io_fk_fields = [
            'entry_by',
            'updated_by',
            'organization',
            'stock',
            'primary_unit',
            'secondary_unit',
        ]
        group_fk_fields = [
            'entry_by',
            'updated_by',
            'organization',
        ]
        order_group_data = self.distributor_order_group.to_dict(
            _exclude=['id', 'alias', ]
        )
        for item in group_fk_fields:
            order_group_data['{}_id'.format(item)] = order_group_data.pop(item)

        order_data = self.to_dict(_exclude=ignore_fields)
        order_data['purchase_date'] = _datetime_now
        order_data['tentative_delivery_date'] = get_tentative_delivery_date(_datetime_now, False)
        order_data['copied_from_id'] = self.id

        if order_invoice_group_id:
            order_data['invoice_group_id'] = order_invoice_group_id
        if delivery_date:
            order_data['tentative_delivery_date'] = delivery_date

        for item in fk_fields:
            order_data['{}_id'.format(item)] = order_data.pop(item)

        io_logs = self.queryset_to_list(
            self.stock_io_logs.filter(status=Status.DISTRIBUTOR_ORDER),
            exclude=ignore_io_fields,
            fk_fields=io_fk_fields
        )

        # Create order group
        distributor_order_group = DistributorOrderGroup.objects.create(**order_group_data)
        # distributor_order_group.save()

        # Create order instance
        order_data['distributor_order_group_id'] = distributor_order_group.id
        order_instance = Purchase.objects.create(**order_data)
        # order_instance.save()

        # Create order items
        for item in io_logs:
            item['date'] = _date_now
            item['purchase_id'] = order_instance.id
            order_item = StockIOLog.objects.create(
                **item
            )
            # order_item.save()

        # Create order tracking instance
        order_tracking = OrderTracking.objects.create(
            order=order_instance,
            entry_by_id=order_instance.entry_by_id
        )
        # order_tracking.save()
        if order_invoice_group_id:
            OrderTracking.objects.create(
                order_status=OrderTrackingStatus.ACCEPTED,
                order=order_instance,
                entry_by_id=order_instance.entry_by_id
            )
        return order_instance, distributor_order_group

    def delete_requisition_related_order_purchase(self, updated_by_id, es_populate_bg = False):
        from procurement.helpers import send_procure_alert_to_slack
        from procurement.models import ProcureGroup

        requisition = self
        # Orders
        purchase_requisitions_connector = PurchaseRequisition.objects.filter(
            status=Status.ACTIVE,
            requisition__id=requisition.id,
            purchase__status=Status.PURCHASE_ORDER
        )
        purchase_order_id_list = []
        purchase_id_list = []

        for item in purchase_requisitions_connector:
            purchases = Purchase.objects.filter(
                copied_from__id=item.purchase_id
            ).only('status', 'id')
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
        # Update procurement
        self.procure_requisitions.filter().update(requisition=None)

        procure_group = ProcureGroup.objects.filter(
            requisition__id=self.id
        )
        if procure_group.exists():
            procure_group = procure_group.first()
            procure_group.requisition = None
            procure_group.save(update_fields=['requisition',])

        if es_populate_bg:
            id_list_for_es_populate = [requisition.id] + purchase_id_list + purchase_order_id_list
            custom_elastic_rebuild('pharmacy.models.Purchase', {'id__in': id_list_for_es_populate})
        # purchase_order_ids = ",".join(map(str, purchase_order_id_list))
        # purchase_ids = ",".join(map(str, purchase_id_list))
        # message = f"Deleted linked Requisition (#{requisition.id}), Purchase Order (#{purchase_order_ids}), Purchase (#{purchase_ids}) for Procure Purchase (#{self.id}) by {self.employee.get_full_name()}."
        # send_procure_alert_to_slack(message)

    @property
    def prev_order_date(self):
        if not self.purchase_date:
            return None
        orders = Purchase.objects.filter(
            id__lt=self.id,
            organization=self.organization_id,
            distributor_id=self.distributor_id,
            purchase_date__lt=self.purchase_date.date()
        ).exclude(
            current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
        ).order_by('-pk')
        if orders.exists():
            return orders.first().purchase_date.date()
        return None

    @property
    def order_number_count(self):
        orders = Purchase.objects.filter(
            id__lt=self.id,
            organization=self.organization_id,
            distributor_id=self.distributor_id,
        ).exclude(
            current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
        ).order_by('-pk')
        return orders.count()

    @property
    def short_total(self):
        shorts = self.short_return_orders.filter(
            status=Status.ACTIVE,
            type=ShortReturnLogType.SHORT
        ).aggregate(
            total_amount=Coalesce(Sum(
                F('short_return_amount') + F('round_discount')
            ), decimal.Decimal(0))
        )
        return shorts.get('total_amount', 0)

    @property
    def return_total(self):
        returns = self.short_return_orders.filter(
            status=Status.ACTIVE,
            type=ShortReturnLogType.RETURN
        ).aggregate(
            total_amount=Coalesce(Sum(
                F('short_return_amount') + F('round_discount')
            ), decimal.Decimal(0))
        )
        return returns.get('total_amount', 0)


    @property
    def procurement_id(self):
        from procurement.models import Procure
        procurement =  Procure.objects.filter(
            status=Status.ACTIVE,
        ).only('id')

        if self.purchase_type == PurchaseType.PURCHASE:
            procurement = procurement.filter(
                requisition__purchase_requisitions__purchases__status=Status.ACTIVE,
                requisition__purchase_requisitions__purchases__id=self.id
            )
        elif self.purchase_type == PurchaseType.ORDER:
            procurement = procurement.filter(
                requisition__purchase_requisitions__status=Status.PURCHASE_ORDER,
                requisition__purchase_requisitions__id=self.id
            )
        elif self.purchase_type == PurchaseType.REQUISITION:
            procurement = procurement.filter(
                requisition__id=self.id
            )
        if procurement.exists() and self.purchase_type in [PurchaseType.PURCHASE, PurchaseType.ORDER, PurchaseType.REQUISITION]:
            return procurement.first().id
        return None

    def get_order_summary(self):
        from ecommerce.models import ShortReturnItem
        from ecommerce.enums import ShortReturnLogType

        short_return_instance = ShortReturnItem.objects.filter(
            short_return_log__order__pk=self.id
        ).only(
            'short_return_log__short_return_amount',
            'short_return_log__round_discount',
            'quantity',
        )
        if short_return_instance.exists():
            order_summary = short_return_instance.aggregate(
                total_order_quantity=Cast(DistinctSum(F('short_return_log__total_order_items')), FloatField()),
                total_order_amount=Round(Coalesce(DistinctSum(Case(When(
                    short_return_log__order__status=Status.DISTRIBUTOR_ORDER,
                    short_return_log__order__distributor_order_type=DistributorOrderType.ORDER,
                    then=F('short_return_log__order__grand_total')),
                    output_field=FloatField())), 0.00)),
                total_short_quantity=Coalesce(Sum(Case(When(
                    status=Status.ACTIVE,
                    type=ShortReturnLogType.SHORT,
                    then=F('quantity')),
                    output_field=FloatField())), 0.00),
                total_short_amount=Coalesce(DistinctSum(Case(When(
                    status=Status.ACTIVE,
                    type=ShortReturnLogType.SHORT,
                    then=F('short_return_log__short_return_amount') + F('short_return_log__round_discount')),
                    output_field=FloatField())), 0.00),
                total_return_quantity=Coalesce(Sum(Case(When(
                    status=Status.ACTIVE,
                    type=ShortReturnLogType.RETURN,
                    then=F('quantity')),
                    output_field=FloatField())), 0.00),
                total_return_amount=Coalesce(DistinctSum(Case(When(
                    status=Status.ACTIVE,
                    type=ShortReturnLogType.RETURN,
                    then=F('short_return_log__short_return_amount') + F('short_return_log__round_discount')),
                    output_field=FloatField())), 0.00),
            )
        else:
            order_summary = Purchase.objects.filter(
                id=self.id
            ).aggregate(
                total_order_quantity=Coalesce(Sum(Case(When(
                    stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                    then=F('stock_io_logs__quantity')))), 0.00),
                total_order_amount=Round(Cast(DistinctSum(F('grand_total')), FloatField())),
            )
            order_summary = {
                'total_order_quantity': order_summary.get('total_order_quantity', 0),
                'total_order_amount':order_summary.get('total_order_amount', 0),
                'total_short_quantity': 0,
                'total_short_amount': 0,
                'total_return_quantity': 0,
                'total_return_amount': 0
            }
        return order_summary

    def get_queryset_for_cache(self, list_of_pks=None, request=None):
        '''
        This method take a list of primary key of Purchase and return queryset to cache them
        Parameters
        ----------
        self : pharmacy.model.Purchase
            An instance of pharmacy.model.Purchase model
        list_of_pks : list
            list of primary key of Purchase it can be None of empty list
        Raises
        ------
        No error is raised by this method
        Returns
        -------
        queryset
            This method return queryset for given Purchase instance's pk
        '''
        if list_of_pks is None or len(list_of_pks) == 0:
            list_of_pks = [self.id]

        queryset = self.__class__.objects.filter(
            pk__in=list_of_pks
        ).select_related(
            'distributor',
            'organization__entry_by',
            'distributor_order_group',
            'responsible_employee__designation__department',
        ).order_by('-id')

        return queryset

    def expire_cache(self, celery=True):
        # get the cache keys for non group order amount
        customer_non_group_order_amount_key_pattern = f"{CUSTOMER_ORG_NON_GROUP_ORDER_GRAND_TOTAL_CACHE_KEY_PREFIX}_{self.organization_id}*"
        customer_delivery_coupon_key_pattern = f"{CUSTOMER_ORG_DELIVERY_COUPON_AVAILABILITY_CACHE_KEY_PREFIX}_{self.organization_id}*"
        keys_for_order_amount_total_of_delivery_date = cache.keys(customer_non_group_order_amount_key_pattern)
        keys_for_delivery_coupon_availability_of_delivery_date = cache.keys(customer_delivery_coupon_key_pattern)
        key_list = [
            'purchase_distributor_order_{}'.format(str(self.id).zfill(12)),
        ]
        # Merge all the keys
        key_list.extend(keys_for_order_amount_total_of_delivery_date)
        key_list.extend(keys_for_delivery_coupon_availability_of_delivery_date)

        if not celery:
            cache.delete_many(key_list)
        else:
            cache_expire_list.apply_async(
                (key_list, ),
                countdown=5,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )

    # Update orderable stock on placing or cancel or rejected order
    def update_related_stocks_orderable_stock(self):
        stocks = Stock.objects.filter(
            stocks_io__purchase__id=self.pk,
            store_point__status=Status.ACTIVE,
        ).only('id', 'orderable_stock', 'stock')
        for stock in stocks:
            stock.save(update_fields=['orderable_stock', 'stock',])

    # Apply additional discount
    def apply_additional_discount(self, discount, percentage=True):
        from .utils import send_push_notification_for_additional_discount
        if percentage:
            additional_discount = ((self.amount - self.discount) * discount) / 100
            additional_discount_rate = discount
        else:
            additional_discount = discount
            additional_discount_rate = (discount * 100) / (self.amount - self.discount)

        additional_discount = round(additional_discount, 3)
        self.additional_discount = additional_discount
        self.additional_discount_rate = round(additional_discount_rate, 3)

        round_discount = self.amount - self.discount - additional_discount
        round_discount = round(round_discount) - round_discount
        round_discount = round(round_discount, 3)
        self.round_discount = round_discount

        self.grand_total = round(self.amount - self.discount - additional_discount + round_discount)

        self.save(update_fields=['additional_discount', 'additional_discount_rate', 'round_discount', 'grand_total'])

        self.distributor_order_group.update_order_amount(order=True)
        # Send push notification to user
        if additional_discount > 0:
            send_push_notification_for_additional_discount(
                self.entry_by_id,
                self.entry_by_id,
                additional_discount,
                self.id
            )

    def update_ecommerce_stock_on_order_or_order_status_change(self):
        from ecommerce.models import ShortReturnItem
        from .utils import get_is_queueing_item_value, get_item_from_list_of_dict
        from pharmacy.helpers import (
            stop_inventory_signal,
            start_inventory_signal,
        )
        from search.tasks import update_stock_document_lazy
        from .tasks import fix_stock_on_mismatch_and_send_log_to_mm

        stock_instances = []
        product_instances = []
        stock_cache_key_list = []

        orderable_stock_update_statuses = [
            OrderTrackingStatus.PENDING,
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED,
        ]

        order_trackings = self.order_status.only('pk', 'order_status',).order_by('-pk')
        stock_update_statuses = [
            OrderTrackingStatus.ON_THE_WAY,
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED,
        ]

        should_update_orderable_stock = (
            (self.current_order_status in orderable_stock_update_statuses and not self.is_queueing_order and order_trackings.count() <= 2)
            or (self.is_queueing_order and self.current_order_status == OrderTrackingStatus.ACCEPTED)
        )
        order_trackings_on_the_way = order_trackings.filter(
            order_status=OrderTrackingStatus.ON_THE_WAY
        )
        already_have_order_trackings_on_the_way = order_trackings_on_the_way.count() > 1
        should_update_orderable_stock_and_ecom_stock_decrease = self.current_order_status == OrderTrackingStatus.ON_THE_WAY and not already_have_order_trackings_on_the_way
        current_statuses = [
            OrderTrackingStatus.PENDING,
            OrderTrackingStatus.ACCEPTED,
            OrderTrackingStatus.READY_TO_DELIVER,
            OrderTrackingStatus.IN_QUEUE,
        ]
        is_current_status_valid_for_increase = self.current_order_status in current_statuses
        if order_trackings.count() >= 2:
            last_status_on_the_way = self.order_status.only('pk', 'order_status',).order_by('-pk')[1].order_status == OrderTrackingStatus.ON_THE_WAY
        else:
            last_status_on_the_way = False
        should_update_orderable_stock_and_ecom_stock_increase = (
            is_current_status_valid_for_increase and last_status_on_the_way
        )

        stock_io_logs = StockIOLog.objects.filter(
            purchase_id=self.id
        ).exclude(status=Status.INACTIVE).only('stock_id', 'quantity').order_by()
        aggregated_stock = list(stock_io_logs.values('stock_id').annotate(
            total_quantity=Coalesce(Sum('quantity'), 0.00),
        ))
        short_return_items = ShortReturnItem.objects.filter(
            short_return_log__order__id=self.id
        ).only('stock_id', 'quantity').exclude(
            status=Status.INACTIVE
        ).values(
            'stock_id',
        ).annotate(
            total_quantity = Coalesce(Sum('quantity'), decimal.Decimal(0))
        )

        stop_inventory_signal()
        stock_id_list_for_es_doc_update = []
        for item in aggregated_stock:
            stock_id = item.get('stock_id')
            stock_id_list_for_es_doc_update.append(stock_id)
            stock = Stock.objects.only(
                'ecom_stock',
                'orderable_stock',
                'product_id',
            ).get(pk=item['stock_id'])
            if should_update_orderable_stock:
                current_orderable_stock = stock.get_current_orderable_stock()
                if stock.orderable_stock != current_orderable_stock:
                    stock.orderable_stock = current_orderable_stock
                    # stock.save(update_fields=['orderable_stock'])
                    Stock.objects.bulk_update([stock], ['orderable_stock',], batch_size=10)
                    # stock_instances.append(stock)
            elif should_update_orderable_stock_and_ecom_stock_decrease:
                total_short_return = get_item_from_list_of_dict(
                    list(short_return_items), 'stock_id', item.get('stock_id')
                ).get('total_quantity', 0)
                stock.ecom_stock -= item.get('total_quantity', 0) - float(total_short_return)
                stock.orderable_stock -= item.get('total_quantity', 0) - float(total_short_return)
                # stock.orderable_stock = stock.get_current_orderable_stock(stock.ecom_stock)
                # stock.save(update_fields=['orderable_stock', 'ecom_stock',])
                Stock.objects.bulk_update([stock], ['orderable_stock', 'ecom_stock',], batch_size=10)
                # stock_instances.append(stock)
            elif should_update_orderable_stock_and_ecom_stock_increase:
                total_short_return = get_item_from_list_of_dict(
                    list(short_return_items), 'stock_id', item.get('stock_id')
                ).get('total_quantity', 0)
                stock.ecom_stock += item.get('total_quantity', 0) - float(total_short_return)
                stock.orderable_stock = stock.get_current_orderable_stock(stock.ecom_stock)
                # stock.save(update_fields=['orderable_stock', 'ecom_stock',])
                Stock.objects.bulk_update([stock], ['orderable_stock', 'ecom_stock',], batch_size=10)

            # Check if product is_queueing_item should change or not
            product = Product.objects.only('order_mode', 'is_queueing_item').get(pk=stock.product_id)
            is_queueing_item_value = get_is_queueing_item_value(stock.orderable_stock, product.order_mode)
            if is_queueing_item_value != product.is_queueing_item:
                product.is_queueing_item = is_queueing_item_value
                product_instances.append(product)
            # List for expiring stock cache
            stock_key_list = [
                f"stock_instance_{str(item['stock_id']).zfill(12)}",
                f"{STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX}_{str(item['stock_id']).zfill(12)}"
            ]
            stock_cache_key_list.extend(stock_key_list)
            # Celery Task: Fix stock on mismatch
            # if self.current_order_status in stock_update_statuses:
            #     fix_stock_on_mismatch_and_send_log_to_mm.apply_async(
            #         (stock_id, ),
            #         countdown=5,
            #         retry=True, retry_policy={
            #             'max_retries': 10,
            #             'interval_start': 0,
            #             'interval_step': 0.2,
            #             'interval_max': 0.2,
            #         }
            #     )
        # Stock.objects.bulk_update(stock_instances, ['ecom_stock', 'orderable_stock',], batch_size=1000)
        Product.objects.bulk_update(product_instances, ['is_queueing_item',], batch_size=1000)
        start_inventory_signal()
        # Expire stock cache
        cache_expire_list.apply_async(
            (stock_cache_key_list, ),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        # update ES doc
        filters = {"pk__in": stock_id_list_for_es_doc_update}
        update_stock_document_lazy.apply_async(
            (
                filters,
            ),
            countdown=1,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )

    def get_supplier_rate(self, stock_id):
        from common.enums import Status
        import pandas as pd

        # Find purchase orders of requisition
        order_pk_list = PurchaseRequisition.objects.filter(
            status=Status.ACTIVE,
            requisition__id=self.id,
            purchase__status=Status.PURCHASE_ORDER
        ).values_list('purchase_id', flat=True)

        # Find io logs with orders of requisition and stock id
        purchase_io_logs = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            stock__id=stock_id,
            purchase__copied_from__id__in=order_pk_list
        ).values(
            'purchase_id',
            'rate',
            'quantity',
            'purchase__supplier_id'
        )

        df = pd.DataFrame(purchase_io_logs)
        df.rename(columns = {'purchase__supplier_id':'supplier_id'}, inplace = True)
        return df.to_dict('records')

    @property
    def discount_info(self):
        from django.db.models import Sum
        from common.utils import Round
        from common.healthos_helpers import CustomerHelper
        from common.enums import Status
        from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus
        from pharmacy.utils import get_discount_for_cart_and_order_items

        non_group_order_amount_total = CustomerHelper(
            self.organization_id
        ).get_non_group_total_amount_for_regular_or_pre_order_from_cache(
            delivery_date=str(self.tentative_delivery_date)
        )
        cart_amount_total = self.amount - self.discount + self.round_discount
        order_grand_total = non_group_order_amount_total + cart_amount_total
        # order_grand_total = Purchase.objects.filter(
        #     organization__id=self.organization_id,
        #     tentative_delivery_date=self.tentative_delivery_date,
        #     status=Status.DISTRIBUTOR_ORDER,
        #     distributor_order_type__in=[
        #         DistributorOrderType.CART,
        #         DistributorOrderType.ORDER,
        #     ],
        #     purchase_type=PurchaseType.VENDOR_ORDER,
        #     current_order_status__in=[
        #         OrderTrackingStatus.PENDING,
        #         OrderTrackingStatus.ACCEPTED,
        #         OrderTrackingStatus.IN_QUEUE
        #     ],
        #     invoice_group__isnull=True
        # ).aggregate(
        #     amount_total=Coalesce(Round(Sum('amount') - Sum('discount') + Sum('round_discount')), 0.00)
        # ).get('amount_total', 0)
        context = get_discount_for_cart_and_order_items(
            cart_grand_total=order_grand_total,
            customer_org_id=self.organization_id
        )
        return {
            'cart_and_order_grand_total': round(order_grand_total),
            'amount_to_reach_next_discount_level': context.get('amount_to_reach_next_discount_level', 0),
            'current_discount_percentage': context.get('current_discount_percentage', 0),
            "current_discount_amount": context.get('current_discount_amount', 0),
            'next_discount_percentage': context.get('next_discount_percentage', 0),
            'next_discount_amount': context.get('next_discount_amount', 0),
        }


class DistributorOrderGroup(CreatedAtUpdatedAtBaseModelWithOrganization):
    """
    Define distributor order group.Order from multiple vendor can be placed in a single order, this
    model define the order group
    """
    sub_total = models.FloatField(default=0.0, help_text="SubTotal amount(excluding discount)")
    discount = models.FloatField(default=0.0, help_text='Total Discount amount')
    round_discount = models.FloatField(default=0.0, help_text='Total Round Discount amount')
    order_type = fields.SelectIntegerField(
        blueprint=DistributorOrderType,
        default=DistributorOrderType.CART,
        help_text='Define cart or order'
    )
    group_id = models.UUIDField(
        default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "Distributor Order Group"
        verbose_name_plural = "Distributor Order Groups"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.organization_id)

    @property
    def show_cart_warning(self):
        import time as STRD_TIME
        from common.healthos_helpers import CustomerHelper
        from pharmacy.utils import get_tentative_delivery_date

        customer_helper = CustomerHelper(organization_id=self.organization_id)
        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
        datetime_now = datetime.strptime(
            STRD_TIME.strftime(DATE_TIME_FORMAT, STRD_TIME.localtime()), DATE_TIME_FORMAT
        )
        order_amount = round((self.sub_total - self.discount + self.round_discount), 3)

        regular_order_delivery_date = get_tentative_delivery_date(datetime_now, False)
        pre_order_delivery_date = get_tentative_delivery_date(datetime_now, True)
        is_regular_order_allowed = customer_helper.is_order_allowed(
            delivery_date=regular_order_delivery_date,
            total_amount=order_amount
        )
        is_pre_order_allowed = customer_helper.is_order_allowed(
            delivery_date=pre_order_delivery_date,
            total_amount=order_amount
        )
        should_show_alert = not is_regular_order_allowed and not is_pre_order_allowed
        return should_show_alert

    @property
    def transport(self):
        # distributor_count = self.order_groups.filter(
        #     status=Status.DISTRIBUTOR_ORDER,
        #     organization__id=self.organization.id,
        #     distributor_order_type=DistributorOrderType.CART,
        #     purchase_type=PurchaseType.VENDOR_ORDER,
        #     stock_io_logs__status=Status.DISTRIBUTOR_ORDER
        # ).only('pk').count()
        # if (self.sub_total - self.discount > 1500) or not distributor_count:
        #     return 0
        # return 60 * distributor_count
        return 0

    @property
    def payable_amount(self):
        return round(self.sub_total + self.round_discount + self.transport - self.discount, 2)

    @property
    def total_payable_amount(self):
        order_groups = DistributorOrderGroup.objects.filter(
            group_id=self.group_id
        ).aggregate(
            total_value=Coalesce(Sum('sub_total'), 0.00) - Coalesce(Sum('discount'), 0.00) + Coalesce(Sum('round_discount'), 0.00)
        )
        return round(order_groups.get('total_value', 0), 2)

    # Update amount related data after deleting or editing order/cart
    def update_order_amount(self, order = False):
        sub_total = 0
        discount = 0
        group_round_discount = 0
        distributor_order_type = DistributorOrderType.ORDER if order else DistributorOrderType.CART
        # Find orders of a order group
        orders = self.order_groups.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=self.organization_id,
            purchase_type=PurchaseType.VENDOR_ORDER,
            distributor_order_type=distributor_order_type,
            stock_io_logs__status=Status.DISTRIBUTOR_ORDER
        ).only(
            'id',
            'amount',
            'discount_rate',
            'grand_total',
            'round_discount',
        ).distinct()
        for order in orders:
            # get calculated amount of a specific order
            order_amount_data = order.get_amount()
            if order_amount_data:
                order_sub_total = order_amount_data.get('sub_total', 0)
                order_discount_total = order_amount_data.get('total_discount', 0)
                discount_rate = round(((order_discount_total * 100) / order_sub_total), 3)
                sub_total += order_sub_total + order.additional_cost
                discount += order_discount_total + order.additional_discount
                grand_total = order_sub_total - order_discount_total + order.additional_cost - order.additional_discount
                round_discount = round(round(grand_total) - grand_total, 3)
                group_round_discount += round_discount
                order_data = {
                    'amount': order_sub_total,
                    'discount': order_discount_total,
                    'discount_rate': discount_rate,
                    'grand_total': grand_total + round_discount,
                    'round_discount': round_discount
                }
                order.__dict__.update(**order_data)
                order.save(update_fields=[*order_data])
        self.sub_total = sub_total
        self.discount = discount
        self.round_discount = group_round_discount
        self.save(update_fields=['sub_total', 'discount', 'round_discount',])
        custom_elastic_rebuild(
            'pharmacy.models.Purchase', {'id__in': list(orders.values_list('pk', flat=True))})
        logger.info(f"Updated amount for distributor order group: {self.id}")

    def update_cart(self):
        from .cart_helpers import update_cart
        update_cart(self.organization_id, self.entry_by_id, self)


class OrderTracking(CreatedAtUpdatedAtBaseModel):
    """
    Order Tracking
    """
    date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date time for status changed'
    )
    order_status = fields.SelectIntegerField(
        blueprint=OrderTrackingStatus,
        default=OrderTrackingStatus.PENDING,
        help_text='Define current status of order'
    )
    failed_delivery_reason = fields.SelectIntegerField(
        blueprint=FailedDeliveryReason,
        default=FailedDeliveryReason.DEFAULT,
        help_text='Define reason for a failed delivery'
    )
    order = models.ForeignKey(
        Purchase, models.DO_NOTHING,
        related_name='order_status',
        help_text='The order for tracking')
    remarks = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Order Tracking"
        verbose_name_plural = "Order Trackings"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.order_id, self.order_status)

    @property
    def invoice_group(self):
        return self.order.invoice_group_id if self.order.invoice_group_id else None

    @property
    def delivery_date(self):
        return self.order.invoice_group.delivery_date if self.order.invoice_group_id else None

class PurchaseRequisition(CreatedAtUpdatedAtBaseModelWithOrganization):
    purchase = models.ForeignKey(
        Purchase, models.DO_NOTHING,
        blank=False, null=False, related_name="purchase_of_requisition")
    requisition = models.ForeignKey(
        Purchase, models.DO_NOTHING,
        blank=True, null=True, related_name="requisition_of_purchase")

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Requisition of Purchase"
        verbose_name_plural = "Requisitions of Purchases"
        index_together = (
            'purchase',
            'requisition',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.purchase, self.requisition)


class StockTransferRequisition(CreatedAtUpdatedAtBaseModelWithOrganization):
    stock_transfer = models.ForeignKey(
        StockTransfer, models.DO_NOTHING,
        blank=False, null=False, related_name="stock_transfer_of_requisition")
    requisition = models.ForeignKey(
        StockTransfer, models.DO_NOTHING,
        blank=True, null=True, related_name="requisition_of_stock_transfer")

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Requisition of StockTransfer"
        verbose_name_plural = "Requisitions of StockTransfer"
        index_together = (
            'stock_transfer',
            'requisition',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.stock_transfer, self.requisition)


class SalesReturn(CreatedAtUpdatedAtBaseModelWithOrganization):
    purchase = models.ForeignKey(
        Purchase, models.DO_NOTHING,
        blank=False, null=False, related_name="purchase_of_return_sales")
    sales = models.ForeignKey(
        Sales, models.DO_NOTHING,
        blank=True, null=True, related_name="return_sales_for_purchase")

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Return Sale"
        verbose_name_plural = "Return Sales"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.purchase, self.sales)


class PurchaseReturn(CreatedAtUpdatedAtBaseModelWithOrganization):
    sales = models.ForeignKey(
        Sales, models.DO_NOTHING,
        blank=False, null=False, related_name="purchase_return")
    purchase = models.ForeignKey(
        Purchase, models.DO_NOTHING,
        blank=True, null=True, related_name="return_purchase")

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Return Purchase"
        verbose_name_plural = "Return Purchases"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.sales, self.purchase)


class StockAdjustment(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateField(blank=True, null=True)
    store_point = models.ForeignKey(
        StorePoint, models.DO_NOTHING, blank=False, null=False,
        related_name='stock_adjustment_store_point')
    employee = models.ForeignKey(Person, models.DO_NOTHING, blank=True,
                                 null=True, related_name='stock_adjustment_by')
    person_organization_employee = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='stockadjustment_employee_person_organization',
        blank=True,
        null=True,
        verbose_name=('stock adjustment employee in person organization'),
        db_index=True
    )
    is_product_disbrustment = models.BooleanField(default=False)
    patient = models.ForeignKey(Person, models.DO_NOTHING, blank=True,
                                null=True, related_name='stock_adjustment_patient')
    person_organization_patient = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='stockadjustment_patient_person_organization',
        blank=True,
        null=True,
        verbose_name=('stock adjustment patient in person organization'),
        db_index=True
    )
    patient_admission = models.ForeignKey(
        'clinic.PatientAdmission', models.DO_NOTHING, blank=True, null=True,
        related_name='stock_adjustment_patient_admission')
    service_consumed = models.ForeignKey(
        'clinic.ServiceConsumed', models.DO_NOTHING, blank=True, null=True,
        related_name='service_consumeds', help_text=_('Disbursement for pathology'))
    remarks = models.CharField(max_length=128, blank=True, null=True)
    disbursement_for = fields.SelectIntegerField(
        blueprint=DisbursementFor,
        default=DisbursementFor.DEFAULT
    )
    adjustment_type = fields.SelectIntegerField(
        blueprint=AdjustmentType,
        default=AdjustmentType.MANUAL
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "StockAdjustment"


class EmployeeStorepointAccess(CreatedAtUpdatedAtBaseModelWithOrganization):
    employee = models.ForeignKey(
        Person, models.DO_NOTHING, blank=False, null=False, related_name='store_point_employee')

    person_organization = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='storepoint_access_person_organization',
        blank=True,
        null=True,
        verbose_name=('employee in person organization'),
        db_index=True
    )

    store_point = models.ForeignKey(
        StorePoint, models.DO_NOTHING, blank=False, null=False, related_name='employee_store_point')
    access_status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "EmployeeStorepointAccess"
        unique_together = ('organization', 'employee', 'store_point')

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.store_point, self.employee)


class EmployeeAccountAccess(CreatedAtUpdatedAtBaseModelWithOrganization):
    employee = models.ForeignKey(
        Person, models.DO_NOTHING, blank=False, null=False, related_name='cash_sale_receiver')

    person_organization = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='accounts_access_person_organization',
        blank=True,
        null=True,
        verbose_name=('employee in person organization'),
        db_index=True
    )
    account = models.ForeignKey(
        'account.Accounts', models.DO_NOTHING, blank=False,
        null=False, related_name='cash_sale_account')
    access_status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "EmployeeAccountAccess"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.employee, self.account)


class ProductDisbursementCause(NameSlugDescriptionBaseOrganizationWiseModel):
    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "Product disbursement causes"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{} {}".format(self.id, self.name)


class StockIOLogDisbursementCause(CreatedAtUpdatedAtBaseModelWithOrganization):
    stock_io_log = models.ForeignKey(
        StockIOLog, models.DO_NOTHING,
        blank=False, null=False, related_name="io_log_disbursement_causes")
    disbursement_cause = models.ForeignKey(
        ProductDisbursementCause, models.DO_NOTHING,
        blank=True, null=True, related_name="disbursement_causes_io_log")
    number_of_usage = models.PositiveIntegerField(
        default=None, blank=True, null=True, help_text='Number of time used')

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Disbursement Cause of Stock IO Log"
        verbose_name_plural = "Disbursement Causes of Stock IO Logs"
        index_together = (
            'stock_io_log',
            'disbursement_cause',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(
            self.id, self.stock_io_log, self.disbursement_cause)


class InvoiceFileStorage(FileStorage):
    organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        db_index=True,
        verbose_name=('organization name')
    )
    repeat = models.IntegerField(default=3)
    orders = models.ManyToManyField(
        Purchase, through='pharmacy.OrderInvoiceConnector',
        related_name='invoice_orders'
    )

    def __str__(self):
        return self.get_name()


class OrderInvoiceConnector(CreatedAtUpdatedAtBaseModel):
    order = models.ForeignKey(
        Purchase, models.DO_NOTHING,
        blank=False, null=False
    )
    invoice = models.ForeignKey(
        InvoiceFileStorage, models.DO_NOTHING,
        blank=True, null=True
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.order, self.invoice)


class ProductChangesLogs(CreatedAtUpdatedAtBaseModelWithOrganization):
    product = models.ForeignKey(
        Product,
        models.DO_NOTHING,
        related_name='product_logs'
    )
    name = models.JSONField(blank=True, null=True, default=dict)
    strength = models.JSONField(blank=True, null=True, default=dict)
    generic = models.JSONField(blank=True, null=True, default=dict)
    form = models.JSONField(blank=True, null=True, default=dict)
    manufacturing_company = models.JSONField(blank=True, null=True, default=dict)
    trading_price = models.JSONField(blank=True, null=True, default=dict)
    purchase_price = models.JSONField(blank=True, null=True, default=dict)
    order_limit_per_day = models.JSONField(blank=True, null=True, default=dict)
    order_limit_per_day_mirpur = models.JSONField(blank=True, null=True, default=dict)
    order_limit_per_day_uttara = models.JSONField(blank=True, null=True, default=dict)
    is_published = models.JSONField(blank=True, null=True, default=dict)
    discount_rate = models.JSONField(blank=True, null=True, default=dict)
    order_mode = models.JSONField(blank=True, null=True, default=dict)
    is_flash_item = models.JSONField(blank=True, null=True, default=dict)
    unit_type = models.JSONField(blank=True, null=True, default=dict)
    compartment = models.JSONField(blank=True, null=True, default=dict)
    is_queueing_item = models.JSONField(blank=True, null=True, default=dict)
    is_salesable = models.JSONField(blank=True, null=True, default=dict)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}".format(self.id)


class StockReminder(CreatedAtUpdatedAtBaseModelWithOrganization):
    stock = models.ForeignKey(
        Stock,
        models.DO_NOTHING,
        related_name='stock_restock_reminder'
    )
    preferable_price = models.DecimalField(
        null=True,
        blank=True,
        max_digits=19,
        decimal_places=3,
    )
    reminder_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.stock)

class Damage(CreatedAtUpdatedAtBaseModel):
    total_quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    reported_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='damage_product_reported_by_user',
        db_index=True
    )
    reported_date = models.DateTimeField(auto_now_add=True)
    remark = models.CharField(max_length=255, blank=True)
    invoice_group = models.ForeignKey(
        "ecommerce.OrderInvoiceGroup",
        models.DO_NOTHING,
        blank = True,
        null = True,
        related_name="damage_invoice_group",
    )

    def __str__(self):
        return f"ID: {self.id}"


class DamageProduct(CreatedAtUpdatedAtBaseModel):
    damage = models.ForeignKey(Damage, models.DO_NOTHING, related_name="damage_io")
    stock = models.ForeignKey(
        Stock, models.DO_NOTHING, related_name="damage_product_stock"
    )
    manufacturer_company_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    product_name = models.CharField(max_length=255, blank=True)
    product_image = TimestampVersatileImageField(upload_to='product/images', blank=True, null=True)
    remark = models.CharField(max_length=255, blank=True)
    invoice_group = models.ForeignKey(
        "ecommerce.OrderInvoiceGroup",
        models.DO_NOTHING,
        blank = True,
        null = True,
        related_name="damage_product_invoice_group",
    )
    price = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discounted_price = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    type = models.CharField(
        max_length=30, choices=DamageProductType.choices, default=DamageProductType.RETURN_DAMAGE
    )

    def __str__(self):
        return f"ID: {self.id}- Name: {self.product_name}"


class Recheck(CreatedAtUpdatedAtBaseModel):
    top_sheet = models.ForeignKey(
        "ecommerce.InvoiceGroupDeliverySheet",
        models.DO_NOTHING,
        null = True,
        blank = True,
        related_name='recheck_product_top_sheets'
    )
    rechecked_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='recheck_product_request_by_user',
        db_index=True
    )
    rechecked_date = models.DateTimeField(auto_now_add=True)
    invoice_group = models.ForeignKey(
        "ecommerce.OrderInvoiceGroup",
        models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="recheck_invoice_group",
    )  # TODO: we keep this for now, need to remove it.
    total_missing_quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_extra_quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    recheck_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)

    def __str__(self):
        return f"ID: {self.id}- Recheck User: {self.rechecked_by.person.full_name}"



class RecheckProduct(CreatedAtUpdatedAtBaseModel):
    recheck = models.ForeignKey(Recheck, models.DO_NOTHING, related_name = "recheck_io")
    stock = models.ForeignKey(
        Stock, models.DO_NOTHING, related_name="recheck_product_stock"
    )
    manufacturer_company_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    product_name = models.CharField(max_length=255, blank=True)
    product_image = TimestampVersatileImageField(upload_to='product/images', blank=True, null=True)
    remark = models.CharField(max_length=255, blank=True)
    invoice_group = models.ForeignKey(
        "ecommerce.OrderInvoiceGroup",
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="recheck_item_invoice_group",
    )
    price = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    order_quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    approved_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING, blank=True, null=True, related_name="recheck_product_approved_by_user"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    type = models.CharField(
        max_length=30, choices=RecheckProductType.choices, default=RecheckProductType.EXTRA
    )

    def __str__(self):
        return f"ID: {self.id}- Name: {self.product_name}"


# attach the signals here
pre_save.connect(pre_save_stock_io_log, sender=StockIOLog)
# post_save.connect(post_save_stock_io_log, sender=StockIOLog)
post_delete.connect(post_delete_stock_io_log, sender=StockIOLog)
post_save.connect(post_save_purchase, sender=Purchase)
pre_save.connect(pre_save_product, sender=Product, dispatch_uid='pre_save_product')
post_save.connect(post_save_product, sender=Product)
post_save.connect(post_save_store_point, sender=StorePoint)
post_save.connect(post_save_employee_account_access, sender=EmployeeAccountAccess)
pre_save.connect(pre_save_stock, sender=Stock)
pre_save.connect(pre_stock_adjustment, sender=StockAdjustment)
pre_save.connect(pre_save_stock_transfer, sender=StockTransfer)
post_save.connect(
    post_save_employee_store_point_access,
    sender=EmployeeStorepointAccess
)
post_save.connect(post_save_order_tracking, sender=OrderTracking)
post_save.connect(post_save_stock_reminder, sender=StockReminder)
post_save.connect(post_save_logo_image, sender=ProductManufacturingCompany)
post_save.connect(post_save_logo_image, sender=ProductCategory)
post_save.connect(post_save_logo_image, sender=ProductGroup)
