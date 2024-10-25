# encoding=utf8
# import sys
# sys.setdefaultencoding('utf8')

# for python3 compatibility
from __future__ import division

import json
import os
from datetime import datetime

from future.builtins import round

from django.core.cache import cache
from django.db.utils import OperationalError
from django.db.transaction import TransactionManagementError
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, F, Subquery, Case, When
from django.db.utils import IntegrityError
from django.db.models.functions import Coalesce

from versatileimagefield.image_warmer import VersatileImageFieldWarmer

from common.cache_keys import PRODUCT_STOCK_REMINDER_ORGANIZATION_KEY_PREFIX
from common.cache_helpers import set_or_clear_delivery_date_cache
from common.enums import PublishStatus, Status
from common.helpers import (
    generate_phone_no_for_sending_sms, custom_elastic_rebuild,
    send_message_to_mattermost_by_channel_id,
    get_request_object, get_enum_key_by_value
)
from common.tasks import send_sms
from common.utils import get_healthos_settings

from core.enums import PersonGroupType, JoiningInitiatorChoices, OrganizationType, AllowOrderFrom
from core.utils import get_global_product_category
from core.helpers import get_user_profile_details_from_cache
from core.models import (
    Person,
    PersonOrganization,
    OrganizationSetting,
    Organization,
)
from expo_notification.tasks import send_push_notification_to_mobile_app
from search.tasks import update_stock_document_lazy
from .enums import (
    StockIOType,
    PurchaseType,
    PurchaseOrderStatus,
    AdjustmentType,
    SalesModeType,
    SalesInactiveType,
    OrderTrackingStatus,
    SystemPlatforms,
    DistributorOrderType,
    UnitType,
)


# Batchwise stock of a product
def get_batch_wise_stock(instance):
    from .models import StockIOLog
    # Batchwise summation of product that IN
    stock_io = StockIOLog.objects.filter(
        status=Status.ACTIVE,
        stock=instance.stock_id,
        batch=instance.batch,
    ).values('stock').aggregate(
        qty_in=Coalesce(Sum(Case(When(
            type=StockIOType.INPUT, then=F('quantity')))), 0.00),
        qty_out=Coalesce(Sum(Case(When(
            type=StockIOType.OUT, then=F('quantity')))), 0.00)
    )
    # Subtract stock IN and stock OUT to get batchwise stock of a product
    stock_qty = stock_io['qty_in'] - stock_io['qty_out']
    return stock_qty


def get_quantity_from_conversion_factor(instance):
    quantity = instance.quantity
    if instance.secondary_unit_flag:
        quantity *= instance.conversion_factor
    return quantity


# update organization wise and global count in stock
def update_count_in_stock(stock, instance, increase=False, decrease=False):
    # organizationwise_count io_log count update
    organization_wise = stock.objects.filter(
        product=instance.stock.product_id,
        organization=instance.organization_id
    )
    # TODO: Write a celery task for updating global count
    # global_count io_log count update
    # global_wise = stock.objects.filter(
    #     product=instance.stock.product_id,
    # )

    if increase:
        organization_wise.update(
            organizationwise_count=F('organizationwise_count') + 1
        )
        # global_wise.update(
        #     global_count=F('global_count') + 1
        # )
    if decrease:
        organization_wise.update(
            organizationwise_count=F('organizationwise_count') - 1
        )
        # global_wise.update(
        #     global_count=F('global_count') - 1
        # )


# pylint: disable=unused-argument
@transaction.atomic
def pre_save_stock_io_log(sender, instance, **kwargs):
    """
    adjusts the stock according to product in and out
    """
    from .models import StockIOLog, Stock, Purchase
    from .tasks import fix_stock_on_mismatch_and_send_log_to_mm, check_and_fix_current_stock_lazy

    minimum_stock = 0
    stock_instance = instance.stock
    # get allowed negative stock from organization settings when negative stock allowed
    # org_instance = Organization.objects.only(
    #     'id',
    #     'type',
    # ).get(pk=instance.organization_id)
    # setting = org_instance.get_settings()
    stock_update_fields = []

    # is_distributor_org = org_instance.type == OrganizationType.DISTRIBUTOR
    is_distributor_org = instance.organization_id == int(os.environ.get('DISTRIBUTOR_ORG_ID', 303))
    setting = get_healthos_settings()
    distributor_requisition = False
    invoice_group_id = None
    is_regular_order = False
    if is_distributor_org and instance.purchase_id:
        distributor_requisition = instance.purchase.purchase_type == PurchaseType.REQUISITION
    elif instance.purchase_id:
        purchase_instance = Purchase.objects.only(
            "purchase_type",
            "distributor_order_type",
            "status",
            "is_queueing_order",
            "invoice_group_id",
        ).get(pk=instance.purchase_id)
        is_regular_order = (
            purchase_instance.purchase_type == PurchaseType.VENDOR_ORDER and
            purchase_instance.distributor_order_type == DistributorOrderType.ORDER and
            purchase_instance.status == Status.DISTRIBUTOR_ORDER and
            purchase_instance.is_queueing_order == False
        )
        invoice_group_id = purchase_instance.invoice_group_id

    # fix batch to case sensitive upper case
    if instance.batch and not instance.batch.isupper():
        instance.batch = instance.batch.upper()

    # stockio will added
    if instance._state.adding:
        # load the current stock demand from database
        current_stock_demand = stock_instance.demand
        instance.calculated_price = stock_instance.calculated_price
        instance.calculated_price_organization_wise = stock_instance.calculated_price_organization_wise

        # deal with the stock demands here
        # if instance.status == Status.DRAFT:
        #     stock_instance.demand += current_stock_demand
        # elif instance.status == Status.RELEASED:
        #     stock_instance.demand -= current_stock_demand

        # Validate ecom stock qty for regular order
        if instance.status == Status.DISTRIBUTOR_ORDER and is_regular_order and not invoice_group_id:
            stock_instance.refresh_from_db(fields=('orderable_stock',))
            product_order_mode = stock_instance.get_product_order_mode()
            if stock_instance.orderable_stock < instance.quantity and product_order_mode == AllowOrderFrom.STOCK:
                # product_name = stock_instance.product.full_name
                raise IntegrityError("Stock Changed, Please try again.")
            else:
                stock_instance.orderable_stock -= instance.quantity
                stock_update_fields.extend(['orderable_stock',])
        if instance.status not in [Status.INACTIVE, Status.DISTRIBUTOR_ORDER]:
            instance.quantity = get_quantity_from_conversion_factor(instance)

        # Update ecommerce stock for requisition
        if distributor_requisition and instance.status == Status.DRAFT:
            stock_instance.refresh_from_db(fields=('ecom_stock',))
            stock_instance.ecom_stock += instance.quantity
            stock_update_fields.extend(['ecom_stock', 'orderable_stock',])
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

        # if status is active then update the stock
        if instance.status == Status.ACTIVE:
            # TODO: Completely remove in future
            # if instance.type == StockIOType.INPUT:
            #     stock_instance.refresh_from_db(fields=('stock',))
            #     stock_instance.stock += instance.quantity
            # elif instance.type == StockIOType.OUT:
            #     stock_instance.refresh_from_db(fields=('stock',))
            #     stock_instance.stock -= instance.quantity
            #     stock_qty = get_batch_wise_stock(instance)
            #     """
            #     Check stock is greater than 0 and
            #     Batchwise quantity of a product is greater than current instance quantity
            #     """
            #     if stock_instance.stock < -minimum_stock or \
            #             instance.quantity > stock_qty + minimum_stock:
            #         if instance.sales_id and \
            #                 instance.sales.sales_mode == SalesModeType.OFFLINE:
            #             product_name = stock_instance.product.full_name
            #             if stock_instance.product.form is not None:
            #                 product_name = "{} {}".format(
            #                     stock_instance.product.form.name,
            #                     stock_instance.product.full_name
            #                 )
            #             raise IntegrityError({
            #                 "error": "STOCK_QUANTITY_CAN_NOT_BE_NEGATIVE_OR_MORE_THAN_CURRENT_STOCK",
            #                 "product": product_name,
            #                 "batch": instance.batch,
            #             })
            #         else:
            #             raise IntegrityError(
            #                 "STOCK_QUANTITY_CAN_NOT_BE_NEGATIVE_OR_MORE_THAN_CURRENT_STOCK")

            # if its active that means its either sales or purchase
            # Update the sales_rate for sales only, ignore for purchase return
            if instance.sales_id is not None and not instance.sales.is_purchase_return:
                # sales
                if instance.secondary_unit_flag:
                    # secondary unit was used
                    stock_instance.latest_sale_unit_id = instance.secondary_unit_id
                    if instance.rate > 0:
                        stock_instance.sales_rate = instance.rate / instance.conversion_factor
                else:
                    # primary unit was used
                    stock_instance.latest_sale_unit_id = instance.primary_unit_id
                    if instance.rate > 0:
                        stock_instance.sales_rate = instance.rate

                # distribute round discount of sales to each stock io logs
                if instance.sales.round_discount != 0:
                    try:
                        instance.round_discount = float(
                            instance.sales.round_discount *\
                                instance.quantity * stock_instance.sales_rate
                        ) / instance.sales.amount
                    except ZeroDivisionError:
                        raise IntegrityError("SALES_AMOUNT_IS_NOT_VALID")

            # Update the purchase_rate for purchase only, ignore for sales return
            if instance.purchase_id is not None and not instance.purchase.is_sales_return:
                # purchase
                if instance.secondary_unit_flag:
                    # secondary unit was used
                    stock_instance.latest_purchase_unit_id= instance.secondary_unit_id
                    if instance.rate > 0:
                        stock_instance.purchase_rate = instance.rate / instance.conversion_factor
                else:
                    # primary unit was used
                    stock_instance.latest_purchase_unit_id = instance.primary_unit_id
                    if instance.rate > 0:
                        stock_instance.purchase_rate = instance.rate

                # distribute round discount of purchase to each stock io logs
                if instance.purchase.round_discount != 0:
                    instance.round_discount = float(
                        instance.purchase.round_discount *\
                            instance.quantity * stock_instance.purchase_rate
                    ) / instance.purchase.amount

        if instance.status == Status.PURCHASE_ORDER:
            # if its status is purchase order then it means, stock log was for purchase order
            if instance.purchase_id is not None and instance.rate > 0:
                if instance.secondary_unit_flag:
                    # secondary unit was used
                    stock_instance.order_rate = instance.rate / instance.conversion_factor
                else:
                    # primary unit was used
                    stock_instance.order_rate = instance.rate
        # local io_log count update
        stock_instance.local_count += 1
        # Ignore update for E-Commerce Order / Cart
        if instance.status != Status.DISTRIBUTOR_ORDER:
            stock_instance.save(
                update_fields=[
                    'stock', 'demand', 'sales_rate', 'purchase_rate',
                    'order_rate', 'local_count', 'latest_sale_unit', 'latest_purchase_unit'
                ] + list(set(stock_update_fields))
            )

        # update_count_in_stock_lazy.delay(instance.stock_id, increase=True)

    # stockio will updated
    else:
        stock_io = StockIOLog.objects.only('id', 'status', 'quantity',).get(id=instance.id)

        # check previous status was active and current status inactive
        if (stock_io.status == Status.ACTIVE or distributor_requisition) \
                and instance.status in [Status.INACTIVE, Status.SUSPEND]:
            # TODO: completel remove in future
            # if instance.type == StockIOType.INPUT:
            #     stock_instance.stock -= instance.quantity
            #     stock_qty = get_batch_wise_stock(instance)

            #     """
            #     After subtract quantity check stock is greater than 0 and
            #     Batchwise quantity of a product is greater than delete quantity
            #     """
            #     if stock_instance.stock < -minimum_stock or \
            #             instance.quantity > stock_qty + minimum_stock:
            #         raise IntegrityError(
            #             "STOCK_QUANTITY_CAN_NOT_BE_NEGATIVE_OR_MORE_THAN_CURRENT_STOCK")
            # if instance.type == StockIOType.OUT:
            #     stock_instance.stock += instance.quantity

            # Update ecommerce stock for requisition
            if distributor_requisition and stock_io.status == Status.DRAFT and instance.type == StockIOType.INPUT:
                stock_instance.refresh_from_db(fields=('ecom_stock',))
                stock_instance.ecom_stock -= instance.quantity
                stock_update_fields.extend(['ecom_stock', 'orderable_stock',])
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

            stock_instance.save(update_fields=['stock'] + stock_update_fields)

        # check previous status was active and current status is also active
        # TODO: completely remove in future
        # if stock_io.status == Status.ACTIVE \
        #         and instance.status == Status.ACTIVE:
        #     if instance.type == StockIOType.INPUT:
        #         if instance.quantity > stock_io.quantity:
        #             stock_instance.stock += (instance.quantity - stock_io.quantity)

        #         if instance.quantity < stock_io.quantity:
        #             stock_instance.stock -= (stock_io.quantity - instance.quantity)
        #             stock_qty = get_batch_wise_stock(instance)
        #             """
        #             After less quantity updated than existing one
        #             then check stock is greater than 0
        #             """
        #             if stock_instance.stock < -minimum_stock:
        #                 raise IntegrityError(
        #                     "STOCK_QUANTITY_CAN_NOT_BE_NEGATIVE_OR_MORE_THAN_CURRENT_STOCK")

        #         stock_instance.save(update_fields=['stock'])


# pylint: disable=unused-argument
@transaction.atomic
def post_delete_stock_io_log(sender, instance, **kwargs):
    """
    adjusts the stock according to product in and out
    """
    instance.quantity = get_quantity_from_conversion_factor(instance)
    if instance.type == StockIOType.INPUT:
        instance.stock.stock -= instance.quantity
    elif instance.type == StockIOType.OUT:
        instance.stock.stock += instance.quantity

    if instance.stock.stock < 0:
        raise IntegrityError('Stock item can not be negative')

    instance.stock.save(update_fields=['stock'])


# pylint: disable=unused-argument
@transaction.atomic
def post_save_purchase(sender, instance, created, **kwargs):
    """
    adjusts the supplier balance on purchase
    """
    # Expire cache keys
    instance.expire_cache(celery=False)

    person_organization = None

    _instance = instance

    def get_person_organization(obj):
        try:
            person_organization = PersonOrganization.objects.only('id', 'balance').get(
                person=obj.supplier_id,
                person_group=PersonGroupType.SUPPLIER,
                organization=obj.supplier.organization_id
            )
        except PersonOrganization.DoesNotExist:
            person_organization = None

        return person_organization

    if created and instance.status != Status.DISTRIBUTOR_ORDER:
        # validation
        if instance.supplier_id:
            # person organization object already exist no need another query
            if instance.person_organization_supplier_id:
                # prevent query for sales return balance adjustment
                person_organization = instance.person_organization_supplier
            else:
                person_organization = get_person_organization(instance)

        # if instance.status == Status.ACTIVE and instance.supplier is None:
        #     raise IntegrityError('Purchase must have a supplier')

        if instance.vat_rate < 0:
            raise IntegrityError('VAT rate can not be negative')

        if instance.tax_rate < 0:
            raise IntegrityError('TAX rate can not be negative')

        if instance.amount < 0:
            raise IntegrityError('Amount can not be negative')

        # calculate vat_total
        instance.vat_total = round(
            (instance.amount * instance.vat_rate) / 100, 3)
        # calculate tax_total
        instance.tax_total = round(
            (instance.amount - instance.discount) * instance.tax_rate / 100, 3)

        # calculate grand_total
        instance.grand_total = round(
            instance.amount -
            instance.discount +
            instance.round_discount +
            instance.vat_total +
            instance.tax_total -
            instance.additional_discount +
            instance.additional_cost,
            3
        )

        # save the instance
        # instance.save(update_fields=['vat_total', 'tax_total', 'grand_total'])

        if instance.status == Status.ACTIVE:
            # calculate the supplier balance
            if instance.supplier_id:
                instance.supplier.balance -= instance.grand_total + instance.transport
                # and update the supplier balance
                instance.supplier.save(update_fields=['balance'])

            if person_organization:
                person_organization.balance -= instance.grand_total + instance.transport
                person_organization.save(update_fields=['balance'])

        if instance.status == Status.ACTIVE:
            instance.purchase_type = PurchaseType.PURCHASE
        elif instance.status == Status.PURCHASE_ORDER:
            instance.purchase_type = PurchaseType.ORDER
        elif instance.status == Status.DRAFT:
            instance.purchase_type = PurchaseType.REQUISITION

        # save the instance
        instance.save(update_fields=['purchase_type', 'vat_total', 'tax_total', 'grand_total'])

#  if update any purchase then supplier balance will be change
    else:
        from .models import StockIOLog
        if instance.status == Status.ACTIVE:
            # calculate vat_total and grand total when purchase updated
            vat = round((instance.amount * instance.vat_rate) / 100, 3)
            if vat != instance.vat_total:
                instance.vat_total = vat
                # calculate grand_total
                instance.grand_total = round(
                    instance.amount -
                    instance.discount +
                    instance.round_discount +
                    instance.vat_total,
                    3
                )
                instance.save(update_fields=['vat_total', 'grand_total'])
        if instance.status == Status.INACTIVE:
            stock_ios = StockIOLog.objects.filter(purchase=instance.id).only(
                'id',
                'alias',
                'status',
                'data_entry_status',
                'round_discount',
                'calculated_price_organization_wise',
                'calculated_price',
                'secondary_unit_flag',
                'rate',
                'quantity',
                'type',
                'batch',
                'conversion_factor',
                'tax_total',
                'tax_rate',
                'vat_rate',
                'vat_total',
                'tax_total',
                'discount_rate',
                'discount_total',
                'purchase_id',
                'primary_unit_id',
                'secondary_unit_id',
                'entry_by_id',
                'updated_by_id',
                'created_at',
                'updated_at',
                'organization_wise_serial',
                'stock_id',
                'transfer_id',
                'sales_id',
                'adjustment_id',
                'organization_id',
                'calculated_price',
                'calculated_price_organization_wise',
                'expire_date',
                'date',
            )
            # if deleted a sales return then transaction is reform
            if instance.is_sales_return:
                transactions = instance.purchases_transaction.filter(
                    status=Status.ACTIVE
                )
                for transaction_ in transactions:
                    transaction_.status = Status.INACTIVE
                    transaction_.save(update_fields=['status'])
                # update supplier(customer) balance (increase)
                if instance.person_organization_supplier_id:
                    instance.person_organization_supplier.balance += instance.grand_total
                    instance.person_organization_supplier.save(update_fields=['balance'])
            for stock_io in stock_ios:
                if stock_io.status != Status.INACTIVE:
                    stock_io.status = Status.INACTIVE
                    stock_io.save(update_fields=['status',])

            # If deleted and purchase order status completed then change it to pending
            if (instance.copied_from and
                    instance.copied_from.purchase_order_status == PurchaseOrderStatus.COMPLETED):
                instance.copied_from.purchase_order_status = PurchaseOrderStatus.PENDING
                instance.copied_from.save(
                    update_fields=['purchase_order_status'])

        if instance.supplier:
            person_organization = get_person_organization(instance)
            if person_organization:
                person_organization.balance += instance.grand_total + instance.transport
            # and update the supplier balance
            instance.supplier.save(update_fields=['balance'])

        # Create Delivery Instance
        # if (_instance.responsible_employee_id and
        #         _instance.current_order_status == OrderTrackingStatus.READY_TO_DELIVER):
        #     _instance.create_delivery_instance()

    # Expire cache keys
    instance.expire_cache()

def pre_save_product(sender, instance, **kwargs):
    from .helpers import get_product_short_name
    from .models import ProductChangesLogs
    from .models import Stock
    from .utils import calculate_product_price
    from .tasks import remind_orgs_on_product_re_stock


    if not instance._state.adding:
        prev_product = sender.objects.get(pk=instance.pk)
        old_instance = {
            'name': prev_product.name,
            'strength': prev_product.strength,
            'generic': prev_product.generic,
            'form': prev_product.form,
            'manufacturing_company': prev_product.manufacturing_company,
            'trading_price': prev_product.trading_price,
            'purchase_price': prev_product.purchase_price,
            'order_limit_per_day': prev_product.order_limit_per_day,
            'order_limit_per_day_mirpur': prev_product.order_limit_per_day_mirpur,
            'order_limit_per_day_uttara': prev_product.order_limit_per_day_uttara,
            'is_published': prev_product.is_published,
            'discount_rate': prev_product.discount_rate,
            'order_mode': prev_product.order_mode,
            'is_flash_item': prev_product.is_flash_item,
            'unit_type': prev_product.unit_type,
            'compartment': prev_product.compartment,
            'is_queueing_item': prev_product.is_queueing_item,
            'is_salesable': prev_product.is_salesable,
        }
        current_instance = {
            'name': instance.name,
            'strength': instance.strength,
            'generic': instance.generic,
            'form': instance.form,
            'manufacturing_company': instance.manufacturing_company,
            'trading_price': instance.trading_price,
            'purchase_price': instance.purchase_price,
            'order_limit_per_day': instance.order_limit_per_day,
            'order_limit_per_day_mirpur': instance.order_limit_per_day_mirpur,
            'order_limit_per_day_uttara': instance.order_limit_per_day_uttara,
            'is_published': instance.is_published,
            'discount_rate': instance.discount_rate,
            'order_mode': instance.order_mode,
            'is_flash_item': instance.is_flash_item,
            'unit_type': instance.unit_type,
            'compartment': instance.compartment,
            'is_queueing_item': instance.is_queueing_item,
            'is_salesable': instance.is_salesable,
        }
        diff = {key: {'Previous': str(old_instance[key]), 'New': str(current_instance[key])}
                for key in old_instance if key in current_instance and old_instance[key] != current_instance[key]}
        if diff:
            ProductChangesLogs.objects.create(
                product=instance,
                name=diff.get('name'),
                strength=diff.get('strength'),
                generic=diff.get('generic'),
                form=diff.get('form'),
                manufacturing_company=diff.get('manufacturing_company'),
                trading_price=diff.get('trading_price'),
                purchase_price=diff.get('purchase_price'),
                order_limit_per_day=diff.get('order_limit_per_day'),
                order_limit_per_day_mirpur=diff.get('order_limit_per_day_mirpur'),
                order_limit_per_day_uttara=diff.get('order_limit_per_day_uttara'),
                is_published=diff.get('is_published'),
                discount_rate=diff.get('discount_rate'),
                order_mode=diff.get('order_mode'),
                is_flash_item=diff.get('is_flash_item'),
                unit_type=diff.get('unit_type'),
                compartment=diff.get('compartment'),
                is_queueing_item=diff.get('is_queueing_item'),
                is_salesable=diff.get('is_salesable'),
                entry_by_id=instance.updated_by_id,
                organization=instance.organization,
                updated_by=instance.updated_by,
                updated_at=instance.updated_at,
                date=datetime.now(),
            )
            # get the current user name
            request = get_request_object()
            user = request.user.get_full_name() if request is not None else None
            product_name = get_product_short_name(instance)
            stock_id = Stock.objects.filter(product=instance).values_list('id', flat=True).first()
            updated_at = str(datetime.now().strftime("%I:%M %p, %d %B, %Y"))
            changes = ''
            for key, value in diff.items():
                if key == 'unit_type':
                    changes += f'{key}: {get_enum_key_by_value(UnitType, int(value["Previous"]))} -> {get_enum_key_by_value(UnitType, int(value["New"]))}'
                elif key == 'order_mode':
                    changes += f'{key}: {get_enum_key_by_value(AllowOrderFrom, int(value["Previous"]))} -> {get_enum_key_by_value(AllowOrderFrom, int(value["New"]))}'
                else:
                    changes += f'\n {key}: {value["Previous"]} -> {value["New"]},'
            message = f'**{user}** has updated product **{product_name}** (ID: #{instance.id}) (Stock ID: #{stock_id}) at **{updated_at}**.\n' \
                      f'Changes: {changes}'
            channel_id = os.environ.get('PRODUCT_CHANGE_LOG_CHANNEL_ID')
            send_message_to_mattermost_by_channel_id(
                channel_id=channel_id,
                message=message,
            )

        # Check if the product has any stock instance and send notification to the organizations if the product price
        # is decreased
        stock = Stock.objects.filter(
            product_id=instance.id,
        ).only('id', 'ecom_stock', 'is_salesable')

        if stock.exists():
            stock = stock.first()
            prev_product_price = calculate_product_price(prev_product.trading_price, prev_product.discount_rate)
            product_price = calculate_product_price(instance.trading_price, instance.discount_rate)
            if product_price < prev_product_price and stock.ecom_stock > 0 and stock.is_salesable == True:
                product_name = get_product_short_name(instance)
                remind_orgs_on_product_re_stock.apply_async(
                    (stock.id, product_name, product_price),
                    countdown=2,
                    retry=True, retry_policy={
                        'max_retries': 10,
                        'interval_start': 0,
                        'interval_step': 0.2,
                        'interval_max': 0.2,
                    }
                )

        # Update Product related stocks last publish unpublish date time if product publish status changed."""
        if old_instance['is_published'] != current_instance['is_published']:
            current_date_time = timezone.now()
            if instance.is_published:
                # Update last_publish date time
                Stock.objects.filter(
                    organization_id=instance.organization_id,
                    status=Status.ACTIVE,
                    product_id=instance.id,
                ).update(
                    last_publish=current_date_time
                )
            elif not instance.is_published:
                # Update last_unpublish date time
                Stock.objects.filter(
                    organization_id=instance.organization_id,
                    status=Status.ACTIVE,
                    product_id=instance.id,
                ).update(
                    last_unpublish=current_date_time
                )


# pylint: disable=unused-argument
@transaction.atomic
def post_save_product(sender, instance, created, **kwargs):
    from .helpers import get_product_short_name
    """
    adjusts the stock according to product in and out
    """
    if instance.display_name is None or instance.display_name=="":
        instance.display_name = get_product_short_name(instance)
        instance.save(update_fields=['display_name'])

    if instance.status == Status.ACTIVE:
        # prepare or check full_name of product
        # lets assume product had valid name
        full_name = str(instance.name)
        rack_name = ""
        if instance.name is None:
            # product name is none then assign empty string
            full_name = ""

        if instance.strength:
            # if had strength append strength
            full_name = "{} {}".format(instance.name, instance.strength)

        if instance.full_name != full_name:
            instance.full_name = full_name
            instance.save(update_fields=['full_name'])
        # Concat alias_name with full_name for making the search with alias name too
        lower_full_name_with_alias = ' '.join(
            filter(None, [full_name, instance.alias_name])
        ).lower()
        full_name_len = len(lower_full_name_with_alias)
        if instance.compartment_id:
            rack_name = instance.compartment.name

    # lazy load
    from .models import StorePoint, Stock

    # Send message to mattermost while creating a new product
    request = get_request_object()
    if created and request is not None:
        user = instance.entry_by.get_full_name() if instance.entry_by_id else None
        created_at = str(datetime.now().strftime("%I:%M %p, %d %B, %Y"))

        instance_id = instance.id
        stock_id = Stock.objects.filter(product=instance).values_list('id', flat=True).first()

        product_name = get_product_short_name(instance)
        strength = instance.strength
        unit_type = instance.unit_type
        unit_type = get_enum_key_by_value(UnitType, unit_type)
        manufacturer = instance.manufacturing_company
        form = instance.form
        generic = instance.generic
        trading_price = instance.trading_price
        purchase_price = instance.purchase_price
        primary_unit = instance.primary_unit
        discount_rate = instance.discount_rate
        order_limit_per_day = instance.order_limit_per_day
        order_mode = instance.order_mode
        compartment = instance.compartment

        message = f'**{user}** has created product **{product_name}** (ID: **{instance_id}**) (Stock ID: {stock_id}) at **{created_at}**.\n' \
                f' Name: {product_name},\n' \
                f' Strength: {strength},\n' \
                f' Unit Type: {unit_type},\n' \
                f' Manufacturer: {manufacturer},\n' \
                f' Form: {form},\n' \
                f' Generic: {generic},\n' \
                f' Trading Price: {trading_price},\n' \
                f' Purchase Price: {purchase_price},\n' \
                f' Primary Unit: {primary_unit},\n' \
                f' Discount Rate: {discount_rate},\n' \
                f' Order Limit Per Day: {order_limit_per_day},\n' \
                f' Order Mode: {order_mode},\n' \
                f' Compartment: {compartment},\n'

        message = message.replace('#', '')
        channel_id = os.environ.get('PRODUCT_CHANGE_LOG_CHANNEL_ID')
        send_message_to_mattermost_by_channel_id(
            channel_id=channel_id,
            message=message,
        )
    if created and not instance.clone:
        # create stock for all the store points for this product
        data_list = []  # for holding data for bulk create
        store_points = []

        # get current organization store point if private product
        if instance.is_global == PublishStatus.PRIVATE:
            store_points = StorePoint.objects.filter(
                organization=instance.organization,
                status=Status.ACTIVE
            )

        # get all organization store point if global product and
        # organization use global product and store point access global product
        elif instance.is_global == PublishStatus.INITIALLY_GLOBAL:
            store_points = StorePoint.objects.filter(
                status=Status.ACTIVE,
                organization__show_global_product=True,
                organization__organizationsetting__global_product_category=instance.global_category,
                populate_global_product=True,
            )

        for store_point_instance in store_points:
            data_list.append(Stock(
                organization=store_point_instance.organization,
                store_point=store_point_instance,
                product=instance,
                display_name=instance.display_name,
                is_service=instance.is_service,
                is_salesable=instance.is_salesable,
                product_full_name=lower_full_name_with_alias,
                product_len=full_name_len,
                rack=rack_name,
                last_publish= instance.created_at if instance.is_published else None,
                last_unpublish = instance.created_at if not instance.is_published else None,

            ))

        stock = Stock.objects.bulk_create(data_list)
    else:
        # product was edited
        if instance.status == Status.ACTIVE:
            # fixing mismatch of service edit
            Stock.objects.filter(
                organization_id=instance.organization_id,
                status=Status.ACTIVE,
                product_id=instance.id,
            ).filter(
                ~Q(is_service=instance.is_service) |
                ~Q(is_salesable=instance.is_salesable)
            ).update(
                is_service=instance.is_service,
                is_salesable=instance.is_salesable
            )

            # fixing mismatch of product name and length
            Stock.objects.filter(
                organization=instance.organization,
                status=Status.ACTIVE,
                product=instance,
            ).filter(
                ~Q(product_full_name=lower_full_name_with_alias) |
                ~Q(product_len=full_name_len) |
                ~Q(rack=rack_name) |
                ~Q(display_name=instance.display_name)
            ).update(
                product_full_name=lower_full_name_with_alias,
                product_len=full_name_len,
                rack=rack_name,
                display_name=instance.display_name
            )
        else:
            Stock.objects.filter(
                product=instance,
            ).filter(
                ~Q(status=instance.status)
            ).update(
                status=instance.status
            )

    if instance.image:
        product_img_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=instance,
            rendition_key_set='product_images',
            image_attr='image',
        )
        num_created, failed_to_create = product_img_warmer.warm()

    is_distributor = Organization.objects.only(
        'type').get(pk=instance.organization_id).type == OrganizationType.DISTRIBUTOR
    if is_distributor:
        instance.update_queueing_item_value()

    instance.expire_cache()
    filters = {"product_id": instance.id}
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

@transaction.atomic
def pre_stock_adjustment(sender, instance, **kwargs):
    """ adjusts the stock """

    from .models import StockAdjustment
    if not instance._state.adding:
        stock_adjustment = StockAdjustment.objects.get(id=instance.id)
        if stock_adjustment.status == Status.ACTIVE \
                and instance.status == Status.INACTIVE:
            stock_io_logs = instance.stock_io_logs.all()
            for stock_io in stock_io_logs:
                stock_io.status = Status.INACTIVE
                # stock_io.stock.save(update_fields=['stock'])
                stock_io.save(update_fields=['status'])


# pylint: disable=unused-argument
@transaction.atomic
def post_save_store_point(sender, instance, created, **kwargs):
    """
    adjusts the stock according to product in and out
    """
    # lazy load
    from .models import Product, Stock, StockAdjustment
    if created:
        # create stock for all the store points for this product
        data_list = []   # for holding data for bulk create
        # create stock for global products if populate global product true
        if instance.populate_global_product and \
                instance.organization.show_global_product:
            products = Product.objects.filter(
                (Q(is_global=PublishStatus.INITIALLY_GLOBAL) |
                 Q(is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
                 Q(organization=instance.organization)) &
                Q(status=Status.ACTIVE),
                global_category__in=get_global_product_category(instance.organization)
            )
        else:
            products = Product.objects.filter(
                is_global=PublishStatus.PRIVATE,
                organization=instance.organization,
                status=Status.ACTIVE
            )

        # discarded_list = Subquery(instance.organization.discarded_products.values('pk'))
        # products = products.exclude(pk__in=discarded_list)
        for product_instance in products:
            data_list.append(Stock(
                organization=instance.organization,
                store_point=instance,
                product=product_instance,
                is_service=product_instance.is_service,
                is_salesable=product_instance.is_salesable,
                product_full_name=product_instance.full_name.lower(),
                product_len=len(product_instance.full_name)
            ))

        stock = Stock.objects.bulk_create(data_list)

        # create a stock adjustment with this storepoint providing adjustment_type=True
        adjustment = StockAdjustment.objects.create(
            organization=instance.organization,
            date=instance.created_at,
            entry_by=instance.entry_by,
            employee=instance.entry_by,
            person_organization_employee=instance.get_person_organization_of_entry_by(),
            store_point=instance,
            adjustment_type=AdjustmentType.AUTO,
        )
        adjustment.save()

        if instance.status == Status.ACTIVE or instance.status == Status.DRAFT:
            from pharmacy.models import EmployeeStorepointAccess

            for item in Person.objects.filter(
                    organization=instance.organization,
                    person_group=PersonGroupType.EMPLOYEE,
                    status=Status.ACTIVE):
                query = EmployeeStorepointAccess.objects.create(
                    organization=instance.organization,
                    employee=item,
                    store_point=instance,
                    person_organization=item.get_person_organization_for_employee(
                        item.organization)
                )
                query.save()


@transaction.atomic
def pre_save_stock_transfer(sender, instance, **kwargs):
    """ adjusts the stock transfer"""

    from .models import StockTransfer
    if not instance._state.adding:
        stock_transfer = StockTransfer.objects.get(id=instance.id)
        if stock_transfer.status == Status.ACTIVE \
                and instance.status == Status.INACTIVE:
            stock_io_logs = instance.stock_io_logs.all()
            for stock_io in stock_io_logs:
                stock_io.status = Status.INACTIVE
                stock_io.save(update_fields=['status'])


@transaction.atomic
def pre_save_stock(sender, instance, **kwargs):
    from .utils import get_is_queueing_item_value
    from .helpers import get_product_short_name
    from .utils import calculate_product_price
    from .tasks import remind_orgs_on_product_re_stock

    """
    adjusts the tracked field of Stocks based on Stock of
    default storepoint containing stock
    """
    if not instance._state.adding:

        from .models import Stock, Product
        prev_stock = instance.__class__.objects.values(
            'orderable_stock',
            'ecom_stock',
            'product__status',
            'product__full_name',
            'product__alias_name',
        ).get(id=instance.id)
        # This part is no longer needed as it was for Hospital Management
        # if prev_stock['tracked'] != instance.tracked:
        #     organization_id = instance.organization_id
        #     product_id = instance.product_id
        #     default_storepoint = instance.organization.get_settings().default_storepoint_id

        #     if default_storepoint:
        #         try:
        #             stock = Stock.objects.values('id', 'tracked').get(
        #                 store_point=default_storepoint,
        #                 product=product_id,
        #                 status=Status.ACTIVE
        #             )
        #             stocks = Stock.objects.filter(
        #                 status=Status.ACTIVE,
        #                 organization=organization_id,
        #                 product=product_id,
        #             ).exclude(tracked=stock['tracked']).count()
        #             if instance.id == stock['id'] and instance.tracked\
        #                     is not stock['tracked'] or stocks > 0:
        #                 Stock.objects.filter(
        #                     status=Status.ACTIVE,
        #                     organization=organization_id,
        #                     product=product_id,
        #                 ).exclude(pk=instance.pk).update(tracked=instance.tracked)
        #             elif instance.id != stock['id'] and instance.tracked is not stock['tracked']:
        #                 instance.tracked = stock['tracked']
        #         except Stock.MultipleObjectsReturned:
        #             raise IntegrityError('Duplicate Stock can\'t be added!')
        #         except Stock.DoesNotExist:
        #             pass

        # Update the product_full_name and product_len if product changed
        # stock = Stock.objects.values(
        #     'product__status',
        #     'product__full_name',
        #     'product__alias_name',
        # ).get(pk=instance.id)
        # if instance.status != stock['product__status']:
        #     from pharmacy.models import OrganizationWiseDiscardedProduct
        #     discarded_products = OrganizationWiseDiscardedProduct.objects.filter(
        #         parent=instance.product_id,
        #         organization=instance.organization_id
        #     ).values_list('pk', flat=True)

        #     if len(discarded_products) == 0:
        #         instance.status = stock['product__status']

        # product_full_name field of stock will be used for search purpose
        # concat product_full_name with alias name for making search with alias_name too
        _product_full_name = ' '.join(
            filter(None, [str(prev_stock['product__full_name']), prev_stock['product__alias_name']])
        )

        if instance.product_full_name != _product_full_name.lower():
            instance.product_full_name = _product_full_name.lower()
            instance.product_len = len(_product_full_name)

        # Update orderable stock on stock change for distributor(e-commerce)
        # org_instance = Organization.objects.only(
        #     'id',
        #     'type',
        # ).get(pk=instance.organization_id)
        # setting = org_instance.get_settings()
        # is_distributor_org = org_instance.type == OrganizationType.DISTRIBUTOR
        should_update_es_doc = False
        is_distributor_org = instance.organization_id == int(os.environ.get('DISTRIBUTOR_ORG_ID', 303))
        if is_distributor_org:
            instance.orderable_stock = instance.get_current_orderable_stock(instance.ecom_stock)
            # Update es doc if orderable stock changed
            should_update_es_doc = instance.orderable_stock != prev_stock["orderable_stock"]
            # Update Next Day Flag
            product = Product.objects.only('order_mode', 'is_queueing_item').get(pk=instance.product_id)
            is_queueing_item_value = get_is_queueing_item_value(instance.orderable_stock, product.order_mode)
            if is_queueing_item_value != product.is_queueing_item:
                should_update_es_doc = True
                product.is_queueing_item = is_queueing_item_value
                Product.objects.bulk_update([product], ['is_queueing_item',], batch_size=1)

        if instance.ecom_stock > prev_stock['ecom_stock'] and instance.ecom_stock > 0 and instance.is_salesable == True:
            should_update_es_doc = True
            stock_id = instance.id
            product_name = get_product_short_name(instance.product)
            product_price = calculate_product_price(instance.product.trading_price, instance.product.discount_rate)
            remind_orgs_on_product_re_stock.apply_async(
                (stock_id, product_name, product_price),
                countdown=2,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )
        # Update ES document
        if should_update_es_doc:
            filters = {"pk": instance.id}
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

    instance.expire_cache()

@transaction.atomic
def post_save_employee_account_access(sender, instance, **kwargs):
    from pharmacy.models import EmployeeAccountAccess
    person_organization = instance.person_organization if instance.person_organization \
        else instance.employee.get_person_organization_for_employee(
            instance.organization
        )
    if person_organization:
        key_name = person_organization.get_permission_cache_key(
            EmployeeAccountAccess)
        person_organization.cache_expire(key_name)


@transaction.atomic
def post_save_employee_store_point_access(sender, instance, created, **kwargs):
    from pharmacy.models import EmployeeStorepointAccess
    person_organization = instance.person_organization if instance.person_organization \
        else instance.employee.get_person_organization_for_employee(
            instance.organization
        )
    if person_organization:
        key_name = person_organization.get_permission_cache_key(
            EmployeeStorepointAccess)
        person_organization.cache_expire(key_name)


@transaction.atomic
def post_save_order_tracking(sender, instance, created, **kwargs):
    from .tasks import (
        calculate_profit_by_order_id_lazy,
        update_ecommerce_stock_on_order_or_order_status_change_lazy,
    )
    from pharmacy.models import DistributorOrderGroup, Purchase

    _instance = instance
    order_fields = [
        'id',
        'current_order_status',
        'entry_by_id',
        'alias',
        'tentative_delivery_date',
        'distributor_order_group_id',
        'is_queueing_order',
        'updated_by_id',
        'organization_id',
        'system_platform',
        'invoice_group_id',
        'invoice_group__alias',
    ]
    if _instance.order_status in  [
        OrderTrackingStatus.ACCEPTED,
        OrderTrackingStatus.PENDING,
        OrderTrackingStatus.IN_QUEUE,
        ]:
        order_fields = []
    _order = Purchase.objects.only(
        *order_fields
    ).get(pk=_instance.order_id)
    _order_group = DistributorOrderGroup.objects.only(
        'alias',
        'discount',
        'round_discount',
        'sub_total',
    ).get(
        pk=_order.distributor_order_group_id
    )
    _order_group_alias = _order_group.alias
    allowed_sms_status = [
        OrderTrackingStatus.ACCEPTED,
        OrderTrackingStatus.REJECTED,
        OrderTrackingStatus.ON_THE_WAY
    ]
    allowed_push_notification_status = [
        OrderTrackingStatus.ACCEPTED,
        OrderTrackingStatus.REJECTED,
        OrderTrackingStatus.CANCELLED,
        OrderTrackingStatus.ON_THE_WAY,
        OrderTrackingStatus.PENDING,
        OrderTrackingStatus.IN_QUEUE,
        OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
        OrderTrackingStatus.PORTER_DELIVERED,
        OrderTrackingStatus.PORTER_FAILED_DELIVERED,
        OrderTrackingStatus.PORTER_FULL_RETURN,
    ]

    if _order.current_order_status != _instance.order_status:
        _order.current_order_status = _instance.order_status
        _order.updated_by_id = _instance.entry_by_id
        _order.save(update_fields=['current_order_status', 'updated_by'])
    elif _order.updated_by_id != _instance.entry_by_id:
        _order.updated_by_id = _instance.entry_by_id
        _order.save(update_fields=['updated_by',])

    # Expire organization has order delivery date cache on cancel / reject order order place
    status_to_expire_user_has_order_delivery_date_cache = [
        OrderTrackingStatus.CANCELLED,
        OrderTrackingStatus.REJECTED,
        OrderTrackingStatus.PENDING,
        OrderTrackingStatus.IN_QUEUE
    ]

    # if order canceled for pre or regular need to clear cache
    if _order.current_order_status in status_to_expire_user_has_order_delivery_date_cache:
        # check if order type is pre order
        set_or_clear_delivery_date_cache(
            organization_id=_order.organization_id,
            delivery_date=str(_order.tentative_delivery_date),
            clear=True
        )

    if created and (_instance.order_status in allowed_sms_status or _instance.order_status in allowed_push_notification_status):
        notification_title = ""
        notification_body = ""
        notification_data = {}
        if _order.entry_by_id:
            _user = get_user_profile_details_from_cache(_order.entry_by_id)
            customer_mobile = generate_phone_no_for_sending_sms(_user.phone)
            customer_name = "{} {}".format(_user.first_name, _user.last_name)
        else:
            customer_mobile = generate_phone_no_for_sending_sms(
                _order.organization.primary_mobile)
            customer_name = _order.organization.contact_person
        customer_sms_text = ""
        if _instance.order_status == OrderTrackingStatus.ACCEPTED:
            customer_sms_text = "Hi {}, \nYour order #{} has been Accepted and will be delivered soon.Keep using HealthOS and get exciting offers.".format(
                customer_name,
                _instance.order_id
            )
            notification_title = "Order Status Changed"
            notification_body = "Your order #{} has been Accepted and will be delivered soon.".format(
                _instance.order_id
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.REJECTED:
            customer_sms_text = "Hi {}, \nYour order #{} has been Rejected.Keep using HealthOS and get exciting offers.".format(
                customer_name,
                _instance.order_id
            )
            notification_title = "Order Status Changed"
            notification_body = "Your order #{} has been Rejected.".format(
                _instance.order_id
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.CANCELLED:
            customer_sms_text = "Hi {}, \nYour order #{} has been Cancelled.Keep using HealthOS and get exciting offers.".format(
                customer_name,
                _instance.order_id
            )
            notification_title = "Order Status Changed"
            notification_body = "Your order #{} has been Cancelled.".format(
                _instance.order_id
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias)
            }
        elif _instance.order_status == OrderTrackingStatus.ON_THE_WAY:
            total_payable_amount = _order_group.payable_amount
            customer_sms_text = "Hi {}, \nYour order #{}, Bill: BDT {} have left our distribution hub. You will receive your products today. Keep using HealthOS and get exciting offers.".format(
                customer_name,
                _instance.order_id,
                format(total_payable_amount, '0.2f')
            )
            notification_title = "Order Status Changed"
            notification_body = "Your order #{}, Bill: BDT {} have left our distribution hub. You will receive your products today.".format(
                _instance.order_id,
                format(total_payable_amount, '0.2f')
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.PENDING:
            notification_title = "New Order Placed"
            notification_body = "Successfully placed new order #{}. It will be delivered by {}.".format(
                _instance.order_id,
                str(_order.tentative_delivery_date)
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "order_status": instance.order_status
            }

        elif _instance.order_status == OrderTrackingStatus.IN_QUEUE:
            notification_title = "New Order Placed"
            notification_body = "Successfully placed new order #{}. It will be delivered by {}.".format(
                _instance.order_id,
                str(_order.tentative_delivery_date)
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.PORTER_DELIVERED:
            notification_title = "Order Delivered Successfully"
            notification_body = "Your order #{} has been delivered successfully.".format(
                _instance.order_id,
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "invoice_id": str(_order.invoice_group_id),
                "invoice_alias": str(_order.invoice_group.alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.PORTER_PARTIAL_DELIVERED:
            notification_title = "Order Delivered Partially"
            notification_body = "Your order #{} has been partially delivered.".format(
                _instance.order_id,
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "invoice_id": str(_order.invoice_group_id),
                "invoice_alias": str(_order.invoice_group.alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.PORTER_FAILED_DELIVERED:
            notification_title = "Order Delivery Failed"
            notification_body = "Your order #{} delivery has been failed.".format(
                _instance.order_id,
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "invoice_id": str(_order.invoice_group_id),
                "invoice_alias": str(_order.invoice_group.alias),
                "order_status": instance.order_status
            }
        elif _instance.order_status == OrderTrackingStatus.PORTER_FULL_RETURN:
            notification_title = "Order Returned"
            notification_body = "Your order #{} has been returned.".format(
                _instance.order_id,
            )
            notification_data = {
                "order_alias": str(_order.alias),
                "order_group_alias": str(_order_group_alias),
                "invoice_id": str(_order.invoice_group_id),
                "invoice_alias": str(_order.invoice_group.alias),
                "order_status": instance.order_status
            }
        # Send sms to customer
        if _instance.order_status in allowed_sms_status and _order.system_platform != SystemPlatforms.ANDROID_APP:
            send_sms.delay(customer_mobile, customer_sms_text, _order.organization_id)
        # Send push notification to mobile device
        if notification_title and notification_body and _order.system_platform == SystemPlatforms.ANDROID_APP:
            send_push_notification_to_mobile_app.delay(
                _order.entry_by_id,
                title=notification_title,
                body=notification_body,
                data=notification_data,
                entry_by_id=_instance.entry_by_id
            )

    # Expire cache keys
    _order.expire_cache()

    # Update organization index for last_order_date, this_month_order and last_month_order
    custom_elastic_rebuild(
        'core.models.Organization',
        {'id': _order.organization_id}
    )

    stock_update_realtime_status_list = [
        OrderTrackingStatus.ON_THE_WAY,
        OrderTrackingStatus.PENDING,
    ]

    # Update orderable stock and ecom stock
    if created and _instance.order_status in stock_update_realtime_status_list:
        # Try 3 times for realtime update otherwise send it to celery
        num_attempts = 3
        while num_attempts > 0:
            try:
                _order.update_ecommerce_stock_on_order_or_order_status_change()
                num_attempts = 0
            except (OperationalError, TransactionManagementError) as _:
                num_attempts -= 1
                if num_attempts == 0:
                    update_ecommerce_stock_on_order_or_order_status_change_lazy.apply_async(
                        (
                            _order.id,
                        ),
                        countdown=2,
                        retry=True,
                        retry_policy={
                            'max_retries': 10,
                            'interval_start': 0,
                            'interval_step': 0.2,
                            'interval_max': 0.2,
                        }
                    )
    elif created:
        update_ecommerce_stock_on_order_or_order_status_change_lazy.apply_async(
            (
                _order.id,
            ),
            countdown=2,
            retry=True,
            retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )


    # Calculate and store profit data
    allowed_status_for_calculate_profit = [
        OrderTrackingStatus.IN_QUEUE,
        OrderTrackingStatus.PENDING,
        OrderTrackingStatus.PARITAL_DELIVERED,
        OrderTrackingStatus.DELIVERED,
        OrderTrackingStatus.COMPLETED,
        OrderTrackingStatus.REJECTED,
        OrderTrackingStatus.CANCELLED,
        OrderTrackingStatus.FULL_RETURNED
    ]

    if _order.current_order_status in allowed_status_for_calculate_profit:
        calculate_profit_by_order_id_lazy.apply_async(
            (_order.id, ),
            countdown=5
        )


def post_save_stock_reminder(sender, instance, created, **kwargs):
    # Expire organization wise product stock reminder cache
    organization_id = instance.organization_id
    cache_key = PRODUCT_STOCK_REMINDER_ORGANIZATION_KEY_PREFIX + str(organization_id)
    cache.delete(cache_key)


def post_save_logo_image(sender, instance, created, **kwargs):
    if instance.logo:
        product_manufacturing_company_logo_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=instance,
            rendition_key_set='logo_images',
            image_attr='logo',
        )
        num_created, failed_to_create = product_manufacturing_company_logo_warmer.warm()
