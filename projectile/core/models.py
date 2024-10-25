from __future__ import unicode_literals
import sys
import logging, os
import datetime
import time
import re
import math
import difflib
from copy import copy

from django.utils import timezone
from dotmap import DotMap
import pandas as pd
from validator_collection import validators, checkers

from enumerify import fields

from django.core.validators import MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Sum, FloatField, TextField, Q
from django.db.models.functions import Coalesce, Cast
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.core.validators import MinValueValidator

from simple_history.models import HistoricalRecords

from core.choices import ResetStatus, ResetType, OtpType
from common.lists import COUNTRIES, LANGUAGES, DATEFORMAT
from common.helpers import get_date_range_from_period
from common.fields import TimestampImageField
from common.cache_keys import (
    PERSON_ORG_SUPPLIER_ALIAS_LIST_CACHE_KEY,
    ORDER_ENDING_TIME_CACHE,
    USER_PROFILE_DETAILS_CACHE_KEY_PREFIX,
    PERSON_ORG_TAGGED_SUPPLIER_CACHE_KEY,
    PERSON_ORG_TAGGED_CONTRACTOR_CACHE_KEY,
    AUTH_USER_CACHE_KEY_PREFIX,
    ORG_INSTANCE_CACHE_KEY_PREFIX,
)
from common.cache_helpers import get_or_clear_cumulative_discount_factor
from common.models import (
    CreatedAtUpdatedAtBaseModel,
    NameSlugDescriptionBaseModel,
    NameSlugDescriptionBaseOrganizationWiseModel,
    CreatedAtUpdatedAtBaseModelWithOrganization,
    FileStorage,
    NameSlugDescriptionCodeBaseModel,
)
from common.enums import Status, GlobalCategory
from common.fields import JSONTextField
from clinic.enums import DaysChoice
from common.utils import remove_brackets_from_word
from pharmacy.enums import (
    GlobalProductCategory,
    DistributorOrderType,
    PurchaseType,
    OrderTrackingStatus,
)
from procurement.enums import RecommendationPriority

from .managers import PersonManager
from .enums import (
    PersonGender,
    PersonGroupType,
    PersonType,
    OrganizationType,
    Themes,
    VatTaxStatus,
    PaginationType,
    ServiceConsumedPrintType,
    ServiceConsumedReceiptType,
    JoiningInitiatorChoices,
    SerialType,
    DiscountType,
    PriceType,
    SalaryType,
    PrintConfiguration,
    SalaryDisburseTypes,
    SalaryHeadType,
    SalaryHeadDisburseType,
    Packages,
    EntryMode,
    PatientInfoType,
    DhakaThana,
    IssueTrackingStatus,
    IssueTypes,
    FilePurposes,
    LoginFailureReason,
    AllowOrderFrom,
)

from .signals import (
    delete_images, post_save_employee,
    post_save_organization,
    pre_save_organization,
    pre_save_organization_settings,
    pre_save_group_permission,
    post_save_person,
    pre_save_person_organization,
    post_save_issue_status,
    post_save_script_file_storage,
    post_save_delivery_hub,
    post_save_area,
    pre_save_password_reset,
)
from .mixins import UserThumbFieldMixin

logger = logging.getLogger(__name__)


class Organization(NameSlugDescriptionBaseModel):
    address = models.CharField(max_length=255)
    logo = TimestampImageField(
        upload_to='organization/logo', blank=True, null=True)
    primary_mobile = models.CharField(max_length=20)
    other_contact = models.CharField(max_length=64, blank=True, null=True)
    contact_person = models.CharField(max_length=64)
    contact_person_designation = models.CharField(max_length=64)
    email = models.CharField(max_length=64, blank=True, null=True)
    copies_while_print = models.TextField(blank=True, null=True)
    show_global_product = models.BooleanField(
        default=False,
        help_text=_('Settings for show global products')
    )
    type = fields.SelectIntegerField(
        blueprint=OrganizationType, default=OrganizationType.MOTHER)
    # Distributor/Buyer organization related fields starts here
    license_no = models.CharField(max_length=128, blank=True, null=True)
    license_image = TimestampImageField(
        upload_to='organization/license', blank=True, null=True)
    delivery_hub = models.ForeignKey(
        'core.DeliveryHub',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='delivery_hub_organizations',
    )
    delivery_thana = fields.SelectIntegerField(
        blueprint=DhakaThana,
        blank=True,
        null=True,
        default=None,
    )
    delivery_sub_area = models.CharField(max_length=128, blank=True, null=True)
    min_order_amount = models.FloatField(default=0.0)
    rating = models.IntegerField(
        default=5,
        validators=[MaxValueValidator(5), MinValueValidator(0)],
        help_text='Ratings of an organization'
    )
    active_issue_count = models.IntegerField(
        default=0,
        help_text='Active issue count of an organization'
    )
    offer_rules = JSONTextField(blank=True, null=True, default='[]')
    referrer = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='referred_organizations',
        blank=True,
        null=True,
        verbose_name=('Person Organization who referred this organization'),
    )
    primary_responsible_person = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='primary_responsible_person_organizations',
        blank=True,
        null=True,
        verbose_name=('Person Organization who are primary responsible person of this organization'),
    )
    secondary_responsible_person = models.ForeignKey(
        'core.PersonOrganization',
        models.DO_NOTHING,
        related_name='secondary_responsible_person_organizations',
        blank=True,
        null=True,
        verbose_name=('Person Organization who are secondary responsible person of this organization'),
    )
    geo_location = models.JSONField(
        blank=True,
        null=True,
        default=dict,
    )
    area = models.ForeignKey(
        'core.Area',
        models.DO_NOTHING,
        related_name='area_organizations',
        blank=True,
        null=True,
        help_text='Area of an organization'
    )
    has_dynamic_discount_factor = models.BooleanField(default=False)
    discount_factor = models.DecimalField(max_digits=19, decimal_places=3, default=0.00)

    # Distributor/Buyer organization related fields ends here
    # history is to keep the historical data of the model
    history = HistoricalRecords()

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.name)

    @property
    def order_ending_time(self):
        try:
            return self.get_settings().order_ending_time
        except:
            return "09:00:00"

    def get_organization_by_name(self, organization_name):
        try:
            return Organization.objects.get(
                name=organization_name,
                status=Status.ACTIVE
            )
        except Organization.DoesNotExist:
            return None

    class Meta:
        ordering = ('name',)

    def get_all_organizations(self):
        return Organization.objects.all()

    def update_settings(self, data=None):
        if data is not None:
            OrganizationSetting.objects.filter(
                organization=self,
                status=Status.ACTIVE
            ).update(**data)

    def get_settings(self):
        org_settings = cache.get(self.get_key())
        if org_settings is None:
            org_settings = OrganizationSetting.objects.filter(organization=self.id).first()
            timeout = 604800 # 7 days (7*24*60*60)
            cache.set(self.get_key(), org_settings, timeout)
        return org_settings

    def get_settings_instance(self):
        org_settings = OrganizationSetting.objects.filter(
            organization=self.id,
            status=Status.ACTIVE
        ).first()
        return org_settings

    # def get_global_category(self):
    #     category = self.get_settings().global_product_category
    #     if category == GlobalProductCategory.DEFAULT:
    #         return [GlobalProductCategory.DEFAULT]
    #     return [category, GlobalProductCategory.DEFAULT]

    def get_key(self):
        return "organization_settings_{}".format(self.id)

    def expire_serial_cache(self):
        cache.delete_pattern("serial_{}_*".format(self.id), itersize=10000)

    def expire_cache(self, expire_user_details_cache=True, celery=True):
        from common.tasks import cache_expire_list

        if expire_user_details_cache:
            user_details_cache_keys = []
            person_pks = self.person_set.filter(
                status=Status.ACTIVE,
                organization_id=self.id
            ).exclude(
                person_group=PersonGroupType.PATIENT
            ).values_list('pk', flat=True)
            for _pk in person_pks:
                user_details_cache_keys.append('core_person_profile_details_{}'.format(_pk))

            # if celery:
            #     cache_expire_list.apply_async(
            #         (user_details_cache_keys, ),
            #         countdown=5,
            #         retry=True, retry_policy={
            #             'max_retries': 10,
            #             'interval_start': 0,
            #             'interval_step': 0.2,
            #             'interval_max': 0.2,
            #         }
            #     )
            # else:
            cache.delete_many(user_details_cache_keys)
            logger.info("Deleted user profile details cache 'core_person_profile_details_xxxx'")

        settings_caches = [
            self.get_key(),
            f"core_custom_serializer_organization_setting_list_{str(self.get_settings().id).zfill(12)}",
            ORDER_ENDING_TIME_CACHE,
            f"{ORG_INSTANCE_CACHE_KEY_PREFIX}{self.id}"
        ]
        logger.info(
            "Deleted organization settings, order ending time and org instance cache"
        )

        # if celery:
        #     cache_expire_list.apply_async(
        #         (settings_caches,),
        #         countdown=5,
        #         retry=True, retry_policy={
        #             'max_retries': 10,
        #             'interval_start': 0,
        #             'interval_step': 0.2,
        #             'interval_max': 0.2,
        #         }
        #     )
        # else:
        cache.delete_many(settings_caches)
        # Delete cumulative discount factor cache
        get_or_clear_cumulative_discount_factor(organization_id=self.id, clear=True)

    def get_active_organizations(self):
        return Organization.objects.filter(status=Status.ACTIVE)

    def get_filtered_organizations(self, _filter):
        return Organization.objects.filter(**_filter)


    def get_cart_group_cache_key(self):
        return f"cart_group_{self.id}"

    # Return organizationwise cart group
    def get_or_add_cart_group(self, data = None, only_fields = [], set_cache = False):
        from pharmacy.models import DistributorOrderGroup
        cache_key = self.get_cart_group_cache_key()
        group_data = cache.get(cache_key)

        if set_cache:
            group_data = group_data if group_data else {}
            group_id = group_data.get('cart_group_id', None)
            if group_data and group_id:
                return group_id
        if data is None:
            data = {}
        try:
            cart_group = DistributorOrderGroup.objects.only(
                *only_fields
            ).get(
                status=Status.ACTIVE,
                organization__id=self.id,
                order_type=DistributorOrderType.CART
            )
        except DistributorOrderGroup.DoesNotExist:
            cart_group = DistributorOrderGroup.objects.create(
                organization_id=self.id,
                order_type=DistributorOrderType.CART,
                **data
            )
        except DistributorOrderGroup.MultipleObjectsReturned:
            cart_group = DistributorOrderGroup.objects.only(*only_fields).filter(
                status=Status.ACTIVE,
                organization__id=self.id,
                order_type=DistributorOrderType.CART
            ).only('pk').first()
            cart_group_pks = DistributorOrderGroup.objects.only(*only_fields).filter(
                status=Status.ACTIVE,
                organization__id=self.id,
                order_type=DistributorOrderType.CART
            ).values_list('pk', flat=True)
            pk_list = list(cart_group_pks[1:])
            DistributorOrderGroup.objects.filter(pk__in=pk_list).update(status=Status.INACTIVE)
        group_data["cart_group_id"] = cart_group.id
        cache.set(cache_key, group_data)
        return cart_group if not set_cache else cart_group.id

    # Return distributorwise cart instance
    def get_or_add_distributorwise_cart(self, data):
        from pharmacy.models import Purchase
        cart_group_id = self.get_or_add_cart_group(set_cache=True)
        try:
            cart_instance = Purchase.objects.get(
                status=Status.DISTRIBUTOR_ORDER,
                organization__id=self.id,
                distributor__id=data.get('distributor_id'),
                is_queueing_order=data.get('is_queueing_order', False),
                distributor_order_type=DistributorOrderType.CART,
                purchase_type=PurchaseType.VENDOR_ORDER,
                distributor_order_group__id=cart_group_id
            )
        except Purchase.DoesNotExist:
            cart_instance = Purchase.objects.create(
                organization_id=self.id,
                status=Status.DISTRIBUTOR_ORDER,
                distributor_order_type=DistributorOrderType.CART,
                purchase_type=PurchaseType.VENDOR_ORDER,
                **data
            )
        except Purchase.MultipleObjectsReturned:
            cart_instance = Purchase.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                organization__id=self,
                distributor__id=data.get('distributor_id'),
                is_queueing_order=data.get('is_queueing_order', False),
                distributor_order_type=DistributorOrderType.CART,
                purchase_type=PurchaseType.VENDOR_ORDER,
                distributor_order_group__id=cart_group_id
            ).first()
        return cart_instance

    def clear_cart(self):
        from pharmacy.models import StockIOLog

        cart_group = self.get_or_add_cart_group(
            only_fields=['id',]
        )
        StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=self.id,
            purchase__distributor_order_type=DistributorOrderType.CART,
            purchase__distributor_order_group__order_type=DistributorOrderType.CART,
            purchase__distributor_order_group__id=cart_group.id
        ).only(
            'id',
            'status',
        ).update(status=Status.INACTIVE)

    # Gel all orders for distributor
    def get_orders_for_distributor(self):
        from django.db.models import Prefetch
        from pharmacy.models import Purchase, StockIOLog
        from pharmacy.enums import DistributorOrderType, PurchaseType
        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor": self,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }
        order_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            purchase__distributor=self
        )
        orders = Purchase.objects.prefetch_related(
            Prefetch('stock_io_logs', queryset=order_items)
        ).filter(**filters)
        return orders

    # Get list of pk of published products company
    def get_company_ids_of_published_products(self):
        from common.utils import get_global_based_discarded_list
        from pharmacy.models import ProductManufacturingCompany

        discarded_lists = get_global_based_discarded_list(
            self, ProductManufacturingCompany, self)
        published_company = ProductManufacturingCompany().get_all_from_organization(
            self,
            Status.ACTIVE,
        ).values_list('pk', flat=True).exclude(pk__in=discarded_lists).filter(
            product_manufacturing_company__status=Status.ACTIVE,
            product_manufacturing_company__is_published=True,
        ).distinct()
        return list(published_company)

    @property
    def last_order_date(self):
        from pharmacy.models import Purchase

        orders = Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=self.id,
            distributor_order_type=DistributorOrderType.ORDER
        ).exclude(
            current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
        ).order_by('-pk')
        if orders.exists():
            return orders.first().purchase_date.date()
        return None

    def total_order(self, filters = None):
        from pharmacy.models import Purchase
        from ecommerce.models import ShortReturnLog

        filters = filters if filters else {}
        # Find orders
        order_id_list = Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=self.id,
            distributor_order_type=DistributorOrderType.ORDER,
            current_order_status__in=[
                OrderTrackingStatus.DELIVERED,
                OrderTrackingStatus.COMPLETED,
                OrderTrackingStatus.PARITAL_DELIVERED
            ],
            **filters
        ).values_list('pk', flat=True)

        # Calculate total order amount
        total_order_amount = Purchase.objects.filter(
            pk__in=order_id_list
        ).aggregate(
            total_amount=Coalesce(Sum(
                'grand_total',
                output_field=FloatField()
            ), 0.00)
        ).get('total_amount', 0)

        # Calculate total short return amount
        total_short_return = ShortReturnLog.objects.filter(
            status=Status.ACTIVE,
            order__id__in=order_id_list,
        ).aggregate(
            total_amount=Coalesce(
                Sum(
                    'short_return_amount',
                    output_field=FloatField()
                ) + Sum(
                    'round_discount',
                    output_field=FloatField()
                ),
                0.00
            )
        ).get('total_amount', 0)

        net_order_amount = total_order_amount - float(total_short_return)
        return net_order_amount

    @property
    def last_month_order_amount(self):

        start_datetime, end_datetime = get_date_range_from_period('LM', True, False)
        filters = {
            'purchase_date__range': [start_datetime, end_datetime]
        }
        return self.total_order(filters)

    @property
    def this_month_order_amount(self):

        start_datetime, end_datetime = get_date_range_from_period('TM', True, False)
        filters = {
            'purchase_date__range': [start_datetime, end_datetime]
        }
        return self.total_order(filters)

    def get_similar_organization_list(self, min_matching_score = 50):
        from operator import itemgetter
        from core.helpers import get_organizations_by_area, get_matching_ratio, fix_stop_words

        organization_to_match = self.to_dict(
            _fields=[
                'id',
                'name',
                'delivery_sub_area',
                'primary_mobile',
                'contact_person',
                'delivery_thana',
                'address',
            ]
        )
        # Get organizations of same area
        organizations = get_organizations_by_area(organization_to_match)
        similar_organizations = []

        for organization in organizations:
            name_matching_score = get_matching_ratio(
                fix_stop_words(organization_to_match.get('name', '')),
                fix_stop_words(organization.get('name', ''))
            )
            if name_matching_score >= min_matching_score:
                owner_name_matching_score = get_matching_ratio(
                    organization_to_match.get('contact_person', ''),
                    organization.get('contact_person', '')
                )
                primary_mobile_matching_score = get_matching_ratio(
                    organization_to_match.get('primary_mobile', ''),
                    organization.get('primary_mobile', '')
                )
                address_matching_score = get_matching_ratio(
                    organization_to_match.get('address', ''),
                    organization.get('address', '')
                )
                organization_data = organization
                organization_data['name_matching_score'] = name_matching_score
                organization_data['owner_name_matching_score'] = owner_name_matching_score
                organization_data['primary_mobile_matching_score'] = primary_mobile_matching_score
                organization_data['address_matching_score'] = address_matching_score
                similar_organizations.append(organization_data)

        return sorted(similar_organizations, key=itemgetter('name_matching_score'), reverse=True)

    def get_po_supplier_alias_list(self):
        """person organization suppliers alias list

        Returns:
            list: list of alias
        """
        from common.tasks import cache_write_lazy

        cache_key = f"{PERSON_ORG_SUPPLIER_ALIAS_LIST_CACHE_KEY}_{self.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        supplier_alias_list = PersonOrganization.objects.filter(
            organization__id=self.id,
            status=Status.ACTIVE,
            person_group=PersonGroupType.SUPPLIER
        ).annotate(
            str_alias=Cast(
                'alias',
                output_field=TextField()
            )
        ).values_list('str_alias', flat=True)
        supplier_alias_list = list(set(supplier_alias_list))
        timeout = 43200
        cache_write_lazy.apply_async(
            args=(cache_key, supplier_alias_list, timeout),
            countdown=1,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        return supplier_alias_list

    @property
    def possible_primary_responsible_person(self):
        last_three_delivery_persons = None
        last_three_delivery_dates = self.invoice_groups.filter(
            status=Status.ACTIVE,
            order_by_organization=self,
            # delivery_date__lt=datetime.date.today(),
            responsible_employee__isnull=False
        ).select_related('order_by_organization').values(
            'id',
            'delivery_date',
            'responsible_employee'
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED
            ]
        ).order_by('-delivery_date').distinct('delivery_date')
        if last_three_delivery_dates.count() >= 3:
            employees = list(last_three_delivery_dates.values_list('responsible_employee', flat=True))
            responsible_employee_id = []
            if len(employees) > 0:
                for index in range(len(employees) - 2):
                    if employees[index] == employees[index + 1] and employees[index + 1] == employees[index + 2]:
                        responsible_employee_id.append(employees[index])
            if len(responsible_employee_id) > 0:
                last_three_delivery_persons = PersonOrganization.objects.get(pk=responsible_employee_id[0])

        return last_three_delivery_persons


class OrganizationSetting(CreatedAtUpdatedAtBaseModel):
    # track_batch = models.BooleanField(
    #     _('batch'),
    #     default=False,
    #     help_text=_('Settings for organization batch')
    # )
    # auto_adjustment = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable auto adjustment')
    # )
    # allow_offline = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable offline')
    # )
    # offline_sales_number = models.PositiveIntegerField(default=100)
    organization = models.OneToOneField(
        Organization, models.DO_NOTHING
    )
    order_ending_time = models.TimeField(
        default=datetime.time(11, 00)
    )
    patient_code_prefix = models.CharField(
        max_length=10,
        default='OMIS'
    )
    # default_discount_rate = models.FloatField(default=0.0)
    # default_vat_rate = models.FloatField(default=0.0)
    # allow_default_discount_vat_rate = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for allowing default discount vat rate in io panel')
    # )
    # service_consumed_receipt_type = fields.SelectIntegerField(
    #     default=ServiceConsumedReceiptType.WITHOUT_QUANTITY,
    #     help_text=_('Service Consumed Receipt Type')
    # )
    # patient_code_length = models.PositiveIntegerField(
    #     validators=[MaxValueValidator(16)],
    #     default=9
    # )
    # patient_schedule_display = models.BooleanField(
    #     default=False
    # )
    # patient_credit_limit = models.BooleanField(
    #     default=False
    # )
    # report_print_header = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for enable/disable report print header')
    # )
    # transaction_head_id = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for transaction head id while transaction add'))
    # Extended fields
    # default_referrer_category = models.ForeignKey(
    #     'core.ReferrerCategory',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='default_of_organization'
    # )
    # default_service = models.ForeignKey(
    #     'clinic.Service',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     help_text=_('select service for sub-service')
    # )
    # default_subservice = models.ForeignKey(
    #     'clinic.SubService',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='sub_service_for_default_service',
    #     help_text=_('select sub-service')
    # )
    date_format = models.CharField(
        max_length=15,
        choices=DATEFORMAT,
        default='dd-MM-yyyy',
        db_index=True
    )
    # cash_sale_transaction_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     help_text=_('select transaction head for cash sale')
    # )
    # sales_return_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     related_name='sales_return_transaction_head'
    # )
    # whole_sale = models.BooleanField(
    #     default=False,
    # )
    # purchase_return_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     related_name='purchase_return_transaction_head'
    # )
    # transfer_from_transaction_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='transaction_head_from'
    # )
    # transfer_to_transaction_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='transaction_head_to'
    # )
    # service_consumed_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='service_consumed_transaction_head'
    # )
    # appointment_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='appointment_head'
    # )
    # admission_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='admission_head'
    # )
    # display_patient_is_positive = models.BooleanField(
    #     default=False
    # )
    # transaction_sms_feature = models.BooleanField(
    #     default=False
    # )
    # appointment_bulk_sms = models.BooleanField(
    #     default=False
    # )
    # show_dependency_disease = models.BooleanField(
    #     default=False
    # )
    # prescriber_designation = models.ManyToManyField(
    #     'EmployeeDesignation',
    #     through='core.PrescriberDesignation',
    #     related_name='settings_prescriber_of_organization'
    # )
    # prescriber_referrer_category = models.ManyToManyField(
    #     'ReferrerCategory',
    #     through='core.PrescriberReferrerCategory',
    #     related_name='settings_prescriber_referrer_category'
    # )
    # trace_admission = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for trace admission')
    # )
    # trace_test_state = models.BooleanField(
    #     _('test_state'),
    #     default=False,
    #     help_text=_('Settings for trace prescription test state')
    # )
    # trace_test_taken_time = models.BooleanField(
    #     _('test_taken_time'),
    #     default=False,
    #     help_text=_('Settings for trace prescription test taken time')
    # )
    # allow_duplicate_person_phone_no = models.BooleanField(
    #     default=True
    # )
    # allow_fingerprint = models.BooleanField(
    #     default=False
    # )
    # allow_service_consumed_due = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for allow due in service consumed of this organization')
    # )
    default_storepoint = models.ForeignKey(
        'pharmacy.StorePoint',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None
    )
    # default_cashpoint = models.ForeignKey(
    #     'account.Accounts',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     default=None,
    #     related_name='settings_default_cash_point'
    # )
    # joining_initiator = fields.SelectIntegerField(
    #     blueprint=JoiningInitiatorChoices,
    #     default=JoiningInitiatorChoices.SALES
    # )

    # joining_initiator_sub_service = models.ForeignKey(
    #     'clinic.SubService',
    #     models.DO_NOTHING,
    #     blank=True,
    #     null=True,
    #     related_name='sub_service_for_joining_date',
    #     help_text=_('select sub-service for joining date')
    # )
    # product_vat_tax_status = fields.SelectIntegerField(
    #     blueprint=VatTaxStatus,
    #     default=VatTaxStatus.DEFAULT,
    #     help_text=_('Choices for product show individual vat, tax and discount or not')
    # )
    # service_consumed_print_type = fields.SelectIntegerField(
    #     blueprint=ServiceConsumedPrintType,
    #     default=ServiceConsumedPrintType.DEFAULT,
    #     help_text=_('Choose service consumed print type')
    # )
    # tube_in_diagnostic_sample = models.BooleanField(
    #     default=False,
    #     help_text=_('allow tube for taking samples')
    # )
    # product_as_tube = models.ForeignKey(
    #     'pharmacy.Product',
    #     models.DO_NOTHING,
    #     blank=True, null=True,
    #     related_name='tube_product',
    #     help_text=_('Choose a default product for using as tube'))
    # show_patient_age = models.BooleanField(
    #     default=False,
    #     help_text=_('Show patient age')
    # )
    # show_patient_economic_status = models.BooleanField(
    #     default=False,
    #     help_text=_('Show patient economic status')
    # )
    # secondary_referrer_head = models.ForeignKey(
    #     'account.TransactionHead',
    #     models.DO_NOTHING,
    #     blank=True, null=True,
    #     related_name='referrer_transaction_head',
    #     help_text=_('Choose a default Transaction head for paying to second referrer')
    # )
    # show_referrer_honorarium = models.BooleanField(
    #     default=False,
    #     help_text=_('Show referrer honorarium')
    # )
    # print_page_header = models.BooleanField(default=True)
    # print_test_name = models.BooleanField(
    #     default=True,
    #     help_text=_('Show / Hide Test Name in Print')
    # )
    # serial_type = fields.SelectIntegerField(
    #     blueprint=SerialType,
    #     default=SerialType.DEFAULT,
    #     help_text=_('Choose Serial/ID type')
    # )
    # discount_type = fields.SelectIntegerField(
    #     blueprint=DiscountType,
    #     default=DiscountType.FLAT,
    #     help_text=_('Choose Discount type')
    # )
    # price_type = fields.SelectIntegerField(
    #     blueprint=PriceType,
    #     default=PriceType.LATEST_PRICE,
    #     help_text=_('Choose which price to show')
    # )
    # show_purchase_price = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for show purchase price as suggestion')
    # )
    # sales_multiple_unit = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for enable multiple unit in sales io panel')
    # )
    # purchase_multiple_unit = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for enable multiple unit in purchase io panel')
    # )
    # bar_code = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable bar code')
    # )
    # multiple_payment = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable multiple payment')
    # )
    # salary_type = fields.SelectIntegerField(
    #     blueprint=SalaryType,
    #     default=SalaryType.BASIC_FROM_GROSS,
    #     help_text=_('Choose for Salary type')
    # )
    # print_configuration = fields.SelectIntegerField(
    #     blueprint=PrintConfiguration,
    #     default=PrintConfiguration.SWAL_ON
    # )
    # global_product_category = fields.SelectIntegerField(
    #     blueprint=GlobalProductCategory,
    #     default=GlobalProductCategory.DEFAULT
    # )
    # global_subservice_category = fields.SelectIntegerField(
    #     blueprint=GlobalCategory,
    #     default=GlobalCategory.DEFAULT
    # )
    # allow_profit_margin = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable Profit Margin')
    # )
    # profit_margin = models.FloatField(
    #     default=0.0,
    #     validators=[MaxValueValidator(100)],
    #     help_text=_('Profit input as percentage(%)')
    # )
    # allow_negative_stock = models.BooleanField(default=False)
    # negative_stock = models.IntegerField(default=0)

    # package = fields.SelectIntegerField(
    #     blueprint=Packages,
    #     default=Packages.PACKAGE_3,
    #     help_text=_('Define different packages for client')
    #     )

    # data_entry_mode = fields.SelectIntegerField(
    #     blueprint=EntryMode,
    #     default=EntryMode.OFF
    # )
    # patient_info_type = fields.SelectIntegerField(
    #     blueprint=PatientInfoType,
    #     default=PatientInfoType.SHORT
    # )

    # allow_discount_margin = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable stock\'s discount Margin')
    # )
    # allow_sale_rate_edit = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for enable/disable sales rate edit')
    # )
    # allow_procurement_product_add_edit = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable product add/edit permission for procurement')
    # )
    # Purchase related settings
    # purchase_product_vat_discount_status = fields.SelectIntegerField(
    #     blueprint=VatTaxStatus,
    #     default=VatTaxStatus.DEFAULT,
    #     help_text=_('Choices for purchase product show individual vat, tax and discount or not')
    # )
    # purchase_discount_type = fields.SelectIntegerField(
    #     blueprint=DiscountType,
    #     default=DiscountType.FLAT,
    #     help_text=_('Choices for Purchase Discount type')
    # )
    # purchase_price_type = fields.SelectIntegerField(
    #     blueprint=PriceType,
    #     default=PriceType.LATEST_PRICE,
    #     help_text=_('Choices for Purchase price type to show')
    # )
    # purchase_default_discount_rate = models.FloatField(default=0.0)
    # purchase_default_vat_rate = models.FloatField(default=0.0)
    # purchase_bar_code = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable Purchase bar code')
    # )
    # purchase_fixed_rate = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable Purchase fix rate')
    # )
    # allow_purchase_default_discount_vat_rate = models.BooleanField(
    #     default=True,
    #     help_text=_('Settings for allowing purchase default discount and vat rate in io operation')
    # )
    # deduct_discount_from_referrer = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable deduct discount from referrer')
    # )
    # patient_tag = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable tag in patient form')
    # )
    # extra_settings = JSONTextField(blank=True, null=True, default='{}')
    # default_service_consumed_overall_discount_status = models.BooleanField(
    #     default=False,
    #     help_text=_('Default value of Service Consumed overall discout')
    # )
    # default_service_consumed_patient_paying_status = models.BooleanField(
    #     default=False,
    #     help_text=_('Default value of Service Consumed patient advanced payment status')
    # )
    # default_service_consumed_referrer_honorarium_status = models.BooleanField(
    #     default=False,
    #     help_text=_('Default value of Service Consumed referrer honorarium')
    # )
    # enable_stock_fixing_celery_task = models.BooleanField(
    #     default=False,
    #     help_text=_('Settings for enable/disable stock fixing celery task')
    # )
    # E-commerce related fields
    allow_order_from = fields.SelectIntegerField(
        blueprint=AllowOrderFrom,
        default=AllowOrderFrom.OPEN,
        help_text=_('Choices for product order from for ecommerce')
    )
    overwrite_order_mode_by_product = models.BooleanField(
        default=False,
        help_text="Decide overwrite order mode from settings or not"
    )

    order_stopping_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Order stopping date')
    )
    order_re_opening_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Order re-opening date')
    )
    order_stopping_message = models.TextField(
        null=True,
        blank=True,
        help_text=_('Order stopping message')
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return f"#{self.id}: {self.organization_id}"

    def get_queryset_for_cache(self, list_of_pks=None, request=None):
        '''
        This method take a list of primary key of OrganizationSettings and return queryset to cache them
        Parameters
        ----------
        self : core.models.OrganizationSettings
            An instance of core.models.OrganizationSettings model
        list_of_pks : list
            list of primary key of Sales it can be None of empty list
        Raises
        ------
        No error is raised by this method
        Returns
        -------
        queryset
            This method return queryset for given OrganizationSettings instance's pk
        '''
        if list_of_pks is None or len(list_of_pks) == 0:
            list_of_pks = [self.id]

        queryset = self.__class__.objects.filter(
            pk__in=list_of_pks
        ).select_related(
            'organization',
        )

        return queryset


class Department(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()


class EmployeeDesignation(NameSlugDescriptionBaseOrganizationWiseModel):
    department = models.ForeignKey(
        Department, models.DO_NOTHING,
        db_index=True
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.department, self.name)


class Person(AbstractBaseUser, PermissionsMixin, CreatedAtUpdatedAtBaseModel, UserThumbFieldMixin):

    """
    A custom User model

    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.

    A more descriptive tutorial can be found here
    http://www.caktusgroup.com/blog/2013/08/07/migrating-custom-user-model-django/
    """
    # Django's default fields
    email = models.EmailField(
        db_index=True,
        unique=False,
        null=True,
        default=None
    )
    phone = models.CharField(
        db_index=True,
        max_length=24,
        unique=False,
        null=True,
        default=None
    )
    first_name = models.CharField(
        max_length=64,
        blank=True
    )
    last_name = models.CharField(
        max_length=64,
        blank=True
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('''Whether this user should be treated as active. Unselect this instead of
        deleting accounts.''')
    )
    country = models.CharField(
        max_length=2,
        choices=COUNTRIES,
        default='bd',
        db_index=True
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGES,
        default='en'
    )
    nid = models.CharField(
        max_length=32,
        default=None,
        blank=True,
        null=True,
        verbose_name=_('NID No.'),
        help_text=_('National ID No. Example: YYYYXXXXXXXXXXXXX')
    )
    profile_image = TimestampImageField(
        upload_to='profiles/pic',
        blank=True,
        null=True
    )
    hero_image = TimestampImageField(
        upload_to='profiles/hero',
        blank=True,
        null=True
    )
    permanent_address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    present_address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    dob = models.DateField(
        blank=True,
        null=True
    )
    person_group = fields.SelectIntegerField(
        blueprint=PersonGroupType,
        default=PersonGroupType.DEFAULT,
        blank=True,
        null=True,
        db_index=True
    )
    person_type = fields.SelectIntegerField(
        blueprint=PersonType,
        default=PersonType.INTERNAL
    )
    balance = models.FloatField(
        default=0
    )
    opening_balance = models.FloatField(
        default=0
    )
    code = models.CharField(
        max_length=16,
        blank=True,
        null=True
    )
    gender = fields.SelectIntegerField(
        blueprint=PersonGender,
        default=PersonGender.MALE
    )
    mothers_name = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    fathers_name = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    designation = models.ForeignKey(
        EmployeeDesignation,
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_index=True
    )
    joining_date = models.DateField(
        blank=True,
        null=True
    )
    registration_number = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    degree = models.CharField(
        max_length=256,
        blank=True,
        null=True
    )
    remarks = models.TextField(
        blank=True,
        null=True
    )
    theme = fields.SelectIntegerField(
        blueprint=Themes,
        default=Themes.DARK
    )

    # fields for supplier account
    company_name = models.CharField(
        max_length=100,
        blank=True
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True
    )
    contact_person_number = models.CharField(
        max_length=100,
        blank=True
    )
    contact_person_address = models.CharField(
        max_length=100,
        blank=True
    )

    objects = PersonManager()
    organization = models.ForeignKey(
        Organization,
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None
    )
    pagination_type = fields.SelectIntegerField(
        blueprint=PaginationType,
        default=PaginationType.SCROLL
    )
    USERNAME_FIELD = 'id'

    # REQUIRED_FIELDS = (,)

    permissions = models.TextField(
        blank=True
    )

    delivery_hub = models.ForeignKey(
        "DeliveryHub",
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name="person_delivery_hub"
    )

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('persons')

    def __str__(self):
        name = u"{} {} - {}".format(
            self.first_name,
            self.last_name,
            self.phone
        )
        return name.strip()

    @property
    def full_name(self):
        name = u"{} {} - {}".format(self.first_name, self.last_name, self.code)
        return name.strip()

    @property
    def current_date(self):
        _date_now = datetime.datetime.strptime(
            time.strftime('%Y-%m-%d', time.localtime()), '%Y-%m-%d').date()
        return _date_now

    def get_full_name(self):
        """ Returns the full name """
        name = u"{} {}".format(
            self.first_name,
            self.last_name,
        )
        return name.strip()

    def get_name_initial(self):
        name = self.get_full_name()
        return "".join([word[0].upper() for word in name.split()])

    def get_profile_object(self):
        return Person.objects.get(pk=self.pk)

    def get_description(self):
        patient_name = self.get_patient_name()
        if self.is_positive:
            description = u"{} - {}".format(patient_name, 'Positive')
        else:
            description = patient_name
        return description.strip()

    def get_schedule_code(self):
        return 0

    def get_person_organization(self):
        try:
            return PersonOrganization.objects.get(
                person_id=self.id,
                organization_id=self.organization.id,
                status=Status.ACTIVE
            )
        except PersonOrganization.DoesNotExist:
            return None

    def get_person_organization_tagged_supplier(self):
        try:
            cache_key = f"{PERSON_ORG_TAGGED_SUPPLIER_CACHE_KEY}{self.id}"
            tagged_supplier_id = cache.get(cache_key)
            if tagged_supplier_id is None:
                person_organization = self.get_person_organization_for_employee(
                    only_fields=['tagged_supplier', ]
                )
                tagged_supplier_id = person_organization.tagged_supplier_id if person_organization else None
                cache.set(cache_key, tagged_supplier_id, 60 * 60 * 24 * 7)
            return tagged_supplier_id
        except:
            return None

    @property
    def has_tagged_supplier(self):
        return self.get_person_organization_tagged_supplier() is not None

    @property
    def tagged_supplier_id(self):
        return self.get_person_organization_tagged_supplier()

    def get_person_organization_tagged_contractor(self):
        try:
            cache_key = f"{PERSON_ORG_TAGGED_CONTRACTOR_CACHE_KEY}{self.id}"
            tagged_contractor_id = cache.get(cache_key)
            if tagged_contractor_id is None:
                person_organization = self.get_person_organization_for_employee(
                    only_fields=['tagged_contractor', ]
                )
                tagged_contractor_id = person_organization.tagged_contractor_id if person_organization else None
                cache.set(cache_key, tagged_contractor_id, 60 * 60 * 24 * 7)
            return tagged_contractor_id
        except:
            return None

    @property
    def has_tagged_contractor(self):
        return self.get_person_organization_tagged_contractor() is not None

    @property
    def tagged_contractor_id(self):
        return self.get_person_organization_tagged_contractor()

    def get_person_organization_for_patient(self):
        try:
            return PersonOrganization.objects.get(
                person=self,
                organization=self.organization,
                person_group=PersonGroupType.PATIENT,
                status=Status.ACTIVE
            )
        except PersonOrganization.DoesNotExist:
            return None

    def get_person_organization_for_employee(self, organization=None, only_fields=None, pk_only=False):
        from core.helpers import get_user_profile_details_from_cache

        if pk_only:
            try:
                user_details = get_user_profile_details_from_cache(self.pk)
                return user_details.person_organization[0].id
            except:
                return self.get_person_organization_for_employee(only_fields=["id"]).id

        person_group = PersonGroupType.EMPLOYEE
        only_fields = only_fields if only_fields else []
        if organization is None:
            filter_organization = self.organization_id
        else:
            filter_organization = organization
        if self.is_superuser:
            person_group = self.person_group

        try:
            return PersonOrganization.objects.only(*only_fields).get(
                status=Status.ACTIVE,
                person=self,
                organization_id=filter_organization,
                person_group=person_group,
            )
        except (PersonOrganization.DoesNotExist, PersonOrganization.MultipleObjectsReturned):
            return None


    def get_person_organization_with_type(self, person_group_type, organization=None, only_fields=None, pk_only=False):
        from core.helpers import get_user_profile_details_from_cache

        person_group = person_group_type
        only_fields = only_fields or []
        if organization is None:
            filter_organization = self.organization_id
        else:
            filter_organization = organization
        if self.is_superuser:
            person_group = self.person_group

        try:
            return PersonOrganization.objects.only(*only_fields).get(
                status=Status.ACTIVE,
                person=self,
                organization_id=filter_organization,
                person_group=person_group,
            )
        except (PersonOrganization.DoesNotExist, PersonOrganization.MultipleObjectsReturned):
            return None


    def get_person_organization_balance(self):

        # to-do fix:
        balance = self.balance

        try:
            person = PersonOrganization.objects.get(
                person=self,
                organization=self.organization,
                status=Status.ACTIVE
            )
            return person.balance

        except PersonOrganization.DoesNotExist:
            return balance

    def get_person_organization_balance_for_patient(self):

        # to-do fix:
        balance = self.balance

        try:
            person = PersonOrganization.objects.get(
                person=self,
                organization=self.organization,
                person_group=PersonGroupType.PATIENT,
                status=Status.ACTIVE
            )
            return person.balance

        except PersonOrganization.DoesNotExist:
            return balance

    def get_person_organization_balance_for_employee(self):

        # to-do fix:
        balance = self.balance

        try:
            person = PersonOrganization.objects.only('id', 'balance',).get(
                person=self,
                organization__id=self.organization_id,
                status=Status.ACTIVE,
                person_group=PersonGroupType.EMPLOYEE,
            )
            return person.balance

        except PersonOrganization.DoesNotExist:
            return balance

    def get_schedule_str(self):
        return None

    # to-do fix:
    def get_opening_balance(self):
        return 0.0

    # Check a user is Admin or Super Admin
    def is_admin_or_super_admin(self):
        return self.does_belongs_to_group_or_admin('Admin') or self.is_superuser

    def is_admin_or_super_admin_or_procurement_manager_or_procurement_coordinator(self):
        return (
            self.is_admin_or_super_admin() or
            self.does_belongs_to_group_or_admin("Procurement Coordinator") or
            self.does_belongs_to_group_or_admin("Procurement Manager") or
            self.does_belongs_to_group_or_admin("Distribution T1")
)
    def has_permission_for_procurement_over_purchase(self):
        return (
            self.does_belongs_to_group_or_admin("ProcurementOverPurchase") and
            (
                self.is_admin_or_super_admin() or
                self.does_belongs_to_group_or_admin("Procurement") or
                self.does_belongs_to_group_or_admin("Procurement Coordinator") or
                self.does_belongs_to_group_or_admin("Procurement Manager")
            )
        )

    def is_delivery_hub_and_not_admin_or_super_admin(self):
        return self.does_belongs_to_group_or_admin("DeliveryHub") and not self.is_admin_or_super_admin()

    def has_permission_for_changing_older_invoice_status(self):
        return self.does_belongs_to_group_or_admin("OlderInvoiceStatusChange")

    def get_username(self):
        return u"{}".format(self.id)

    def get_permission_cache_key(self, group_name):
        if self.organization_id is None:
            organization_id = 0
        else:
            organization_id = self.organization_id
        cache_key = "permission_{}_{}_{}".format(
            str(self.id).zfill(7),
            str(organization_id).zfill(7),
            group_name
        )
        return cache_key

    def get_user_profile_details_cache_key(self):
        cache_key = f"{USER_PROFILE_DETAILS_CACHE_KEY_PREFIX}{self.id}"
        return cache_key

    def get_auth_user_cache_key(self):
        cache_key = f"{AUTH_USER_CACHE_KEY_PREFIX}{self.id}"
        return cache_key

    def delete_user_profile_details_cache(self):
        cache.delete_many(
            [
                self.get_user_profile_details_cache_key(),
                self.get_auth_user_cache_key()
            ]
        )

    @property
    def profile_details(self):
        cache_key = self.get_user_profile_details_cache_key()
        profile_details = cache.get(cache_key)
        if profile_details:
            return DotMap(profile_details)
        return self

    def delete_permission_cache(self):
        permission_pattern = "permission_{}*".format(
            str(self.id).zfill(7)
        )
        cache.delete_pattern(permission_pattern, itersize=10000)

    def does_belongs_to_group_or_admin(self, group_name):

        cache_key = self.get_permission_cache_key(group_name)
        data = cache.get(cache_key)

        if data is None:
            data = list(
                PersonOrganizationGroupPermission.objects.filter(
                    person_organization__in=PersonOrganization.objects.filter(
                        person=self,
                        organization__id=self.organization_id,
                        person_group__in=(PersonGroupType.EMPLOYEE, PersonGroupType.MONITOR),
                        status=Status.ACTIVE
                    ),
                    permission__pk__in=GroupPermission.objects.filter(
                        status=Status.ACTIVE,
                        name__in=[group_name]
                    ).select_related('permission').values_list('id', flat=True)
                    )
                )

            if len(data) > 0:
                cache.set(cache_key, True, 24*60*60)
                return True

            cache.set(cache_key, False, 24*60*60)
            return False

        return data

    def get_stocks_from_recent_orders(self, limit=60):
        from pharmacy.models import Stock
        person = self
        filters = {
            "stocks_io__purchase__status": Status.DISTRIBUTOR_ORDER,
            "stocks_io__purchase__distributor_order_type": DistributorOrderType.ORDER,
            "stocks_io__purchase__purchase_type": PurchaseType.VENDOR_ORDER,
            "stocks_io__purchase__organization__id": person.organization_id
        }

        stocks = Stock.objects.filter(
            **filters
        ).values_list('pk', flat=True).order_by('-stocks_io__pk')
        stocks = list(dict.fromkeys(list(stocks)))
        return stocks[:limit]

    def get_full_name_with_code_or_phone(self):
        if self.code:
            return self.full_name.strip()
        else:
            return self.get_full_name()

    def get_full_name_initial_or_code_from_person_organization(self):
        returned_value = ""
        try:
            person_organization = PersonOrganization.objects.get(
                person=self,
                organization__id=self.organization_id,
                status=Status.ACTIVE,
                person_group=PersonGroupType.EMPLOYEE,
            )
            if person_organization.code and person_organization.code not in ["", "None", "null"]:
                returned_value = person_organization.code
            else:
                returned_value = person_organization.get_name_initial()
        except PersonOrganization.DoesNotExist:
            returned_value = self.get_name_initial()

        return remove_brackets_from_word(returned_value)


class PersonOrganization(CreatedAtUpdatedAtBaseModelWithOrganization, UserThumbFieldMixin):
    person = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='person_organization',
        db_index=True
    )

    person_group = fields.SelectIntegerField(
        blueprint=PersonGroupType,
        default=PersonGroupType.PATIENT,
        blank=True,
        null=True,
        db_index=True
    )

    person_type = fields.SelectIntegerField(
        blueprint=PersonType,
        default=PersonType.INTERNAL
    )

    opening_balance = models.FloatField(default=0)
    balance = models.FloatField(default=0)
    # Django's default fields
    email = models.EmailField(
        null=True,
        default=None
    )
    phone = models.CharField(
        max_length=24,
        null=True,
        default=None
    )
    code = models.CharField(max_length=16, blank=True, null=True)
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    country = models.CharField(
        max_length=2, choices=COUNTRIES, default='bd', db_index=True)
    country_code = models.CharField(max_length=30, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGES, default='en')
    mothers_name = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    fathers_name = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    permanent_address = models.CharField(max_length=255, blank=True, null=True)
    present_address = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = fields.SelectIntegerField(
        blueprint=PersonGender, default=PersonGender.MALE)
    designation = models.ForeignKey(
        EmployeeDesignation,
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_index=True
    )
    joining_date = models.DateField(blank=True, null=True)
    registration_number = models.CharField(
        max_length=64, blank=True, null=True)
    degree = models.CharField(max_length=256, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True)

    contact_person = models.CharField(max_length=100, blank=True)
    contact_person_number = models.CharField(max_length=100, blank=True)
    contact_person_address = models.CharField(max_length=100, blank=True)

    nid = models.CharField(
        max_length=32,
        default=None,
        blank=True,
        null=True,
        verbose_name=_('NID No.'),
        help_text=_('National ID No. Example: YYYYXXXXXXXXXXXXX')
    )
    profile_image = TimestampImageField(
        upload_to='profiles/pic',
        blank=True,
        null=True
    )
    hero_image = TimestampImageField(
        upload_to='profiles/hero',
        blank=True,
        null=True
    )
    default_storepoint = models.ForeignKey(
        'pharmacy.StorePoint',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='person_organization_of_store'
    )
    default_cashpoint = models.ForeignKey(
        'account.Accounts',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='person_organization_of_account'
    )
    # This field will store buyer organization for order
    buyer_organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='organization_buyer'
    )
    # Custom fields
    custom_field_1 = models.CharField(max_length=128, blank=True)
    custom_field_2 = models.CharField(max_length=128, blank=True)
    custom_field_3 = models.CharField(max_length=128, blank=True)
    custom_field_4 = models.CharField(max_length=128, blank=True)

    tagged_supplier = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None
    )

    tagged_contractor = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='tagged_contractors_list'
    )

    permissions = models.TextField(
        blank=True
    )

    delivery_hub = models.ForeignKey(
        "DeliveryHub",
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name="person_organization_delivery_hub"
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = 'Person in Organization'
        verbose_name_plural = "Person in Organizations"
        index_together = [
            ['organization', 'person']
        ]
        unique_together = (
            'person',
            'organization',
            'person_group',
            'status',
        )

    def __str__(self):
        name = u"{} - {}".format(self.person_id, self.organization_id)
        return name.strip()

    def get_person_organization_from_id(self, given_id):

        try:
            return PersonOrganization.objects.get(
                id=given_id
            )
        except PersonOrganization.DoesNotExist:
            return None

    def get_full_name(self):
        """ Returns the full name """
        if self.company_name:
            name = self.company_name
        else:
            name = u"{} {}".format(self.first_name, self.last_name)
        return name

    full_name = property(get_full_name)

    def get_name_initial(self):
        """ Returns the name initial """
        name = self.get_full_name()
        return "".join([word[0].upper() for word in name.split()])

    def is_patient_code_exists(self, code="", organization=None):
        """ Return True if unique else False """
        code_exist = PersonOrganization.objects.filter(
            status=Status.ACTIVE,
            organization=organization,
            code__iexact=code
        ).exists()
        return code_exist

    def get_schedule_str(self):
        return None

    def get_instance_from_code(self, code_str, organization_instance, person_type):
        """Returns the instance from code"""
        try:
            return PersonOrganization.objects.get(
                code=code_str,
                organization=organization_instance,
                person_group=person_type,
                status=Status.ACTIVE
            )
        except PersonOrganization.DoesNotExist:
            return None


    def cache_expire(self, key_name):
        from common.tasks import cache_expire

        # organization_id = str(format(self.organization.id, '04d'))
        # cache_key = '{}_{}'.format(key_name, organization_id)

        cache_expire.apply_async(
            (key_name,),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )


    def get_permission_cache_key(self, model_name):
        """
        return cache key name based on model name
        combined with organization id and employee id
        """
        key_string = re.findall('[A-Z][^A-Z]*', model_name.__name__)
        key_string = '_'.join(key_string).lower()
        return "{}_{}_{}".format(
            key_string, self.organization.id, self.id
        )


    def get_user_permitted_data(self, model_name, selected_field):
        """
        return permitted access data based on permission model from cache
        arguments:
            models_name - permission model name
            selected_field - selected field name on permission model
        """
        cache_key = self.get_permission_cache_key(model_name)
        data = cache.get(cache_key)
        if not data:
            data = model_name.objects.filter(
                status=Status.ACTIVE,
                access_status=True,
                person_organization=self,
            ).values_list(selected_field, flat=True)
            data = list(data)
            timeout = 604800  # 7 days (7*24*60*60)
            cache.set(cache_key, data, timeout)
        return data


    def get_delivery_sheet_number(self, date):
        '''
        Date format: 2022-10-25
        '''
        from ecommerce.models import InvoiceGroupDeliverySheet
        from common.utils import prepare_start_date, prepare_end_date

        start_date = prepare_start_date(date)
        end_date = prepare_end_date(date)
        delivery_sheet_number_count = InvoiceGroupDeliverySheet.objects.filter(
            responsible_employee=self,
            date__range=[start_date, end_date]
        ).only("id").count()
        total_delivery_sheet_number_count = delivery_sheet_number_count + 1
        return total_delivery_sheet_number_count

    def get_delivery_sheet_name(self, date):
        '''
        Date format: 2022-10-25
        '''
        delivery_sheet_number = self.get_delivery_sheet_number(date)
        date = date.replace('-', '_')
        delivery_sheet_name = f'{self.code}_{date}_{delivery_sheet_number}'
        return delivery_sheet_name


    @property
    def manager(self):
        managers = self.managers.filter(status=Status.ACTIVE)
        if managers.exists():
            return managers.first().manager
        else:
            return None

    @manager.setter
    def manager(self, value):
        if self.manager == value:
            return
        old_manager = self.manager
        if old_manager:
            self.managers.filter(manager=old_manager).update(status=Status.INACTIVE)
        self.managers.create(
            manager=value,
            employee=self,
            status=Status.ACTIVE,
            updated_at=self.updated_at,
            updated_by_id=self.updated_by_id,
            entry_by_id=self.entry_by_id
        )

    def set_tagged_supplier_cache(self):
        if self.tagged_supplier_id:
            supplier_id = self.tagged_supplier_id
            person_id = self.person_id
            cache_key = f"{PERSON_ORG_TAGGED_SUPPLIER_CACHE_KEY}{person_id}"
            cache.set(cache_key, supplier_id, 60 * 60 * 24 * 7)

    def rebuild_tagged_supplier_cache(self):
        cache_key = f"{PERSON_ORG_TAGGED_SUPPLIER_CACHE_KEY}{self.person_id}"
        cache.delete(cache_key)
        self.set_tagged_supplier_cache()

    def expire_tagged_supplier_cache(self):
        cache_key = f"{PERSON_ORG_TAGGED_SUPPLIER_CACHE_KEY}{self.person_id}"
        cache.delete(cache_key)

    def set_tagged_contractor_cache(self):
        if self.tagged_contractor_id:
            contractor_id = self.tagged_contractor_id
            person_id = self.person_id
            cache_key = f"{PERSON_ORG_TAGGED_CONTRACTOR_CACHE_KEY}{person_id}"
            cache.set(cache_key, contractor_id, 60 * 60 * 24 * 7)

    def rebuild_tagged_contractor_cache(self):
        cache_key = f"{PERSON_ORG_TAGGED_CONTRACTOR_CACHE_KEY}{self.person_id}"
        cache.delete(cache_key)
        self.set_tagged_contractor_cache()

    def expire_tagged_contractor_cache(self):
        cache_key = f"{PERSON_ORG_TAGGED_CONTRACTOR_CACHE_KEY}{self.person_id}"
        cache.delete(cache_key)


class GroupPermission(NameSlugDescriptionBaseModel):

    class Meta:
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')

        unique_together = (
            'name',
        )

    def __str__(self):
        name = u"{}".format(self.name)
        return name.strip()


class PersonOrganizationGroupPermission(CreatedAtUpdatedAtBaseModel):

    # make sure that status is Inactive by default in serializer
    person_organization = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name="group_permission"
    )
    permission = models.ForeignKey(
        GroupPermission,
        models.DO_NOTHING,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = _('Permission on Organization')
        verbose_name_plural = _('Permissions Organization')

        unique_together = (
            'person_organization',
            'permission',
        )

    def __str__(self):
        name = u"{} - {}".format(self.person_organization, self.permission)
        return name.strip()


class SmsLog(CreatedAtUpdatedAtBaseModelWithOrganization):
    phone_number = models.CharField(max_length=2048)
    sms_body = models.TextField(blank=True, null=True)
    sms_count = models.PositiveIntegerField(blank=True, null=True, default=0)
    response_from_server = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        verbose_name=('organization name')
    )

    def __str__(self):
        name = f"{self.phone_number} - {self.sms_body}"
        return name.strip()


class ScriptFileStorage(FileStorage):
    date = models.DateField(blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    file_purpose = fields.SelectIntegerField(
        blueprint=FilePurposes,
        default=FilePurposes.SCRIPT,
        help_text='Purpose to use of the file'
    )
    data = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text='Prediction params',
    )
    prediction_on = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
    )
    set_stock_from_file = models.BooleanField(default=False)

    # pylint: disable=old-style-class, no-init
    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.get_name()

    def is_valid_prediction_file(self):

        purchase_prediction_columns = [
            'ID',
            'MRP',
            'SP',
            'AVG',
            'L_RATE',
            'H_RATE',
            'KIND',
            'STATUS',
            'OSTOCK',
            'SELL',
            'PUR',
            'SHORT',
            'RET',
            'NSTOCK',
            'PRED',
            'NORDER',
            'D3',
            'SUPPLIER_S1',
            'QTY_S1',
            'RATE_S1',
            'SUPPLIER_S2',
            'QTY_S2',
            'RATE_S2',
            'SUPPLIER_S3',
            'QTY_S3',
            'RATE_S3',
        ]

        stock_df =  pd.read_excel(self.content)
        columns_from_file = stock_df.columns.to_list()
        necessary_columns = []
        for item in columns_from_file:
            match = re.search("SUPPLIER_S", item)
            if match:
                for li in difflib.ndiff(item, "SUPPLIER_S"):
                    if li[0] == '-':
                        suggested_supplier = li[-1]
                        supplier_col_name = f"SUPPLIER_S{suggested_supplier}"
                        qty_col_name = f"QTY_S{suggested_supplier}"
                        rate_col_name = f"RATE_S{suggested_supplier}"
                        necessary_columns.append(supplier_col_name)
                        necessary_columns.append(qty_col_name)
                        necessary_columns.append(rate_col_name)

        purchase_prediction_columns += necessary_columns
        missing_columns = list(set(purchase_prediction_columns) - set(columns_from_file))
        if not missing_columns:
            return True
        return False

    def populate_prediction_data(self, organization_id):
        from common.utils import get_value_or_zero
        from pharmacy.models import Stock
        from pharmacy.tasks import populate_stock_supplier_avg_rate_cache
        from pharmacy.helpers import get_product_short_name
        from procurement.models import PurchasePrediction, PredictionItemSupplier, PredictionItem
        from procurement.enums import RecommendationPriority

        stock_df =  pd.read_excel(self.content)
        row, column = stock_df.shape
        columns_from_file = stock_df.columns.to_list()

        pred_item_suppliers = []
        for item in columns_from_file:
            match = re.search("SUPPLIER_S", item)
            if match:
                for li in difflib.ndiff(item, "SUPPLIER_S"):
                    if li[0] == '-':
                        suggested_supplier = li[-1]
                        priority = RecommendationPriority.OTHER if checkers.is_integer(suggested_supplier) and int(suggested_supplier) > 3 else int(suggested_supplier)
                        supplier_col_name = f"SUPPLIER_S{suggested_supplier}"
                        qty_col_name = f"QTY_S{suggested_supplier}"
                        rate_col_name = f"RATE_S{suggested_supplier}"
                        cols = {
                            "supplier": supplier_col_name,
                            "qty": qty_col_name,
                            "rate": rate_col_name,
                            "priority": priority
                        }
                        pred_item_suppliers.append(cols)

        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
        DATE_FORMAT = '%Y-%m-%d'
        _datetime_now = datetime.datetime.strptime(
            time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
        _date_now = datetime.datetime.strptime(
            time.strftime(DATE_FORMAT, time.localtime()), DATE_FORMAT).date()

        purchase_prediction, _ = PurchasePrediction.objects.get_or_create(
            defaults={'date': _datetime_now, 'is_locked': False},
            prediction_file_id=self.id,
            organization_id=organization_id,
            entry_by_id=self.entry_by_id,
            # label=file.purpose,
        )
        new_instance_count = 0
        existing_instance_count = 0
        exception_str = ""

        try:
            for index, item in stock_df.iterrows():
                stock_id = item.get('ID', '')
                stock = Stock.objects.get(pk=stock_id)
                product_full_name = get_product_short_name(stock.product)
                company_name = stock.product.manufacturing_company.name
                employee_id = item.get('EMP_ID', '')
                assign_to = None
                if not math.isnan(employee_id):
                    is_employee_exist_in_db = PersonOrganization.objects.only('id').filter(pk=employee_id)
                    if is_employee_exist_in_db.exists():
                        assign_to = employee_id

                if not math.isnan(stock_id):
                    # populate_stock_supplier_avg_rate_cache.delay(int(stock_id))
                    check_existing = PredictionItem.objects.filter(
                        status=Status.ACTIVE,
                        stock__id=stock_id,
                        purchase_prediction=purchase_prediction,
                        product_name=product_full_name,
                        company_name=company_name,
                        index=index
                    )

                    if not check_existing.exists():
                        data = {
                            'date': _date_now,
                            'stock_id': stock_id,
                            'mrp': get_value_or_zero(item.get('MRP', 0)),
                            'sale_price': get_value_or_zero(item.get('SP', 0)),
                            'avg_purchase_rate': get_value_or_zero(item.get('AVG', 0)),
                            'lowest_purchase_rate': get_value_or_zero(item.get('L_RATE', 0)),
                            'highest_purchase_rate': get_value_or_zero(item.get('H_RATE', 0)),
                            'margin': 0 if not get_value_or_zero(item.get('AVG', 0)) else (get_value_or_zero(item.get('SP', 0)) - get_value_or_zero(item.get('AVG', 0))) * 100 / get_value_or_zero(item.get('AVG', 0)),
                            'product_visibility_in_catelog': item.get('STATUS', ''),
                            'sold_quantity': get_value_or_zero(item.get('SELL', 0)),
                            'purchase_quantity': get_value_or_zero(item.get('PUR', 0)),
                            'short_quantity': get_value_or_zero(item.get('SHORT', 0)),
                            'return_quantity': get_value_or_zero(item.get('RET', 0)),
                            'new_stock': get_value_or_zero(item.get('NSTOCK', 0)),
                            'prediction': get_value_or_zero(item.get('PRED', 0)),
                            'new_order': get_value_or_zero(item.get('NORDER', 0)),
                            'suggested_purchase_quantity': get_value_or_zero(item.get('D3', 0)),
                            'suggested_min_purchase_quantity': get_value_or_zero(item.get('D1', 0)),
                            'purchase_prediction': purchase_prediction,
                            'organization_id': organization_id,
                            'entry_by_id': self.entry_by_id,
                            'product_name': product_full_name,
                            'company_name': company_name,
                            'real_avg': get_value_or_zero(item.get('RAVG', 0)),
                            'assign_to_id': assign_to,
                            'team': item.get('TEAM', ''),
                            'sale_avg_3d': get_value_or_zero(item.get('3D', 0)),
                            'worst_rate': get_value_or_zero(item.get('WRATE', 0)),
                            'index': index
                        }

                        if data.get('suggested_min_purchase_quantity', 0) > 0:
                            data['has_min_purchase_quantity'] = True

                        prediction_item = PredictionItem.objects.create(**data)
                        new_instance_count += 1

                        for item_supplier in pred_item_suppliers:
                            supplier_id = item.get(item_supplier['supplier'], '')
                            qty = item.get(item_supplier['qty'], 0)
                            rate = item.get(item_supplier['rate'], 0)
                            priority = item_supplier['priority']

                            if not math.isnan(supplier_id):
                                is_supplier_exist_in_db = PersonOrganization.objects.only('id').filter(pk=supplier_id)
                                if is_supplier_exist_in_db.exists():
                                    PredictionItemSupplier.objects.create(
                                        prediction_item=prediction_item,
                                        organization_id=organization_id,
                                        entry_by_id=self.entry_by_id,
                                        supplier_id=int(supplier_id),
                                        rate=get_value_or_zero(rate),
                                        quantity=get_value_or_zero(qty),
                                        priority=priority
                                    )

                    else:
                        existing_instance_count += 1
            return True, exception_str, new_instance_count, row - new_instance_count - existing_instance_count, row

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            return True, exception_str, new_instance_count, row - new_instance_count - existing_instance_count, row

    def populate_prediction_data_from_file(self, organization_id):
        if self.is_valid_prediction_file():
            return self.populate_prediction_data(organization_id)
        else:
            exception_str = "Invalid Prediction File"
            return False, exception_str, 0, 0

    @property
    def is_locked(self):
        return self.stocks_predictions.filter(is_locked=True).exists()


class Issue(CreatedAtUpdatedAtBaseModelWithOrganization):
    """
    Issue Tracking
    """
    date = models.DateTimeField(
        help_text='Date time for issue'
    )
    issue_organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='issues',
        db_index=True,
        help_text='Issue organization'
    )
    type = fields.SelectIntegerField(
        blueprint=IssueTypes,
        default=IssueTypes.OTHERS,
        help_text='Define type of issue'
    )
    order = models.ForeignKey(
        'pharmacy.Purchase', models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='order_issues',
        help_text='The order for related to issue')
    current_issue_status = fields.SelectIntegerField(
        blueprint=IssueTrackingStatus,
        default=IssueTrackingStatus.PENDING,
        help_text='Define current status of issue'
    )
    reported_to = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='person_organization_reported_to'
    )
    reported_against = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='person_organization_reported_against'
    )
    responsible_to_resolve = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='person_organization_responsible_to_resolve'
    )
    remarks = models.TextField(
        blank=True,
        null=True
    )
    invoice_group = models.ForeignKey(
        'ecommerce.OrderInvoiceGroup',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='order_invoice_group_issues',
        help_text='The order invoice group related to issue'
    )

    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.organization, self.issue_status)


class IssueStatus(CreatedAtUpdatedAtBaseModel):
    """
    Issue Status
    """
    date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date time for status changed'
    )
    issue_status = fields.SelectIntegerField(
        blueprint=IssueTrackingStatus,
        default=IssueTrackingStatus.PENDING,
        help_text='Define current status of issue'
    )
    issue = models.ForeignKey(
        Issue, models.DO_NOTHING,
        related_name='issue_status',
        help_text='The issue for status tracking')
    remarks = models.CharField(
        max_length=512,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Issue Status"
        verbose_name_plural = "Issue Statuses"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.issue, self.issue_status)


class AuthLog(CreatedAtUpdatedAtBaseModel):

    password = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=55,
    )
    failure_reason = fields.SelectIntegerField(
        blueprint=LoginFailureReason,
        default=LoginFailureReason.OTHERS,
        help_text='Define current status of issue'
    )
    error_message = models.CharField(max_length=511)

    class Meta:
        verbose_name = _('Authentication Log')
        verbose_name_plural = _('Authentication Logs')

    def __str__(self):
        name = u"{} - {}".format(self.phone, self.failure_reason)
        return name.strip()

class EmployeeManager(CreatedAtUpdatedAtBaseModel):

    employee = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        related_name='managers',
        verbose_name=('employee'),
    )
    manager = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        related_name='employees',
        verbose_name=('employee manager'),
    )

    class Meta:
        verbose_name_plural = "EmployeeManager"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.employee_id, self.manager_id)


class DeliveryHub(NameSlugDescriptionBaseModel):
    address = models.TextField(
        blank=True,
    )
    short_code = models.CharField(
        max_length=12,
        unique=True,
    )
    hub_areas = models.JSONField(
        blank=True,
        null=True,
        default=list,
    )

    class Meta:
        verbose_name = "Delivery Hub"
        verbose_name_plural = "Delivery Hubs"

    def __str__(self):
        return f"{self.name} - {self.short_code}"


class OTP(CreatedAtUpdatedAtBaseModel):
    user = models.ForeignKey(
        'core.Person',
        models.DO_NOTHING,
        related_name="user_otps"
    )
    otp = models.CharField(
        max_length=6,
    )
    type = models.CharField(
        max_length=30,
        choices=OtpType.choices,
        default=OtpType.OTHER,
    )
    is_used = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name_plural="OTP"

    def __str__(self):
        return f"{self.otp} {self.is_used}"


class PasswordReset(NameSlugDescriptionBaseOrganizationWiseModel):
    user = models.ForeignKey(
        'core.Person',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="password_reset_users"
    )
    phone = models.CharField(
        max_length=24,
        db_index=True,
    )
    reset_status = models.CharField(
        max_length=20,
        choices=ResetStatus.choices,
        default=ResetStatus.PENDING,
    )
    otp = models.ForeignKey(
        OTP,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="password_reset_otps"
    )
    type = models.CharField(
        max_length=20,
        choices=ResetType.choices,
        default=ResetType.SELF,
    )
    reset_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "PasswordReset"

    def __str__(self):
        return f"{self.name} - {self.phone}"


class Area(NameSlugDescriptionBaseModel):
    code = models.CharField(max_length=24, unique=True)
    discount_factor = models.DecimalField(max_digits=19, decimal_places=3, default=0.00)

    # history is to keep the historical data of the model
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "Areas"

    def __str__(self):
        return f"{self.name} - {self.code}"


post_save.connect(post_save_person, sender=Person)
post_save.connect(post_save_employee, sender=Person)
post_save.connect(post_save_organization, sender=Organization)
pre_save.connect(pre_save_organization, sender=Organization)
pre_save.connect(pre_save_organization_settings, sender=OrganizationSetting)
pre_save.connect(pre_save_group_permission, sender=PersonOrganizationGroupPermission)
post_delete.connect(delete_images, sender=Person)
pre_save.connect(pre_save_person_organization, sender=PersonOrganization)
post_save.connect(post_save_issue_status, sender=IssueStatus)
post_save.connect(post_save_script_file_storage, sender=ScriptFileStorage)
post_save.connect(post_save_delivery_hub, sender=DeliveryHub)
post_save.connect(post_save_area, sender=Area)
pre_save.connect(pre_save_password_reset, sender=PasswordReset)
