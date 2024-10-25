from datetime import datetime
import time
from copy import deepcopy
from operator import itemgetter
from django.db.models.functions import Coalesce
from django.db.models import Sum, Q
from django.core.cache import cache

from common.enums import Status
from core.enums import AllowOrderFrom
from core.models import Organization
from pharmacy.enums import PurchaseType, DistributorOrderType
from pharmacy.utils import get_item_from_list_of_dict, get_or_create_cart_instance
from pharmacy.models import Stock, StockIOLog, Product, Purchase, DistributorOrderGroup

from .utils import calculate_total_quantity_based_on_various_criteria


def distribute_round_among_cart_items(cart_items, grand_total, round_amount):
    for item in cart_items:
        item_total = (item.get('rate', 0) * item.get('quantity', 0)) - item.get('discount_total', 0)
        item['round_discount'] = float(format((item_total * round_amount) / grand_total, '.3f'))
    return cart_items

def update_or_create(
    item_list,
    update_cart_item_instances,
    create_cart_item_instances,
    org_id,
    cart_instance_id,
    entry_by_id = None,
    is_queueing_order = False,
    io_log_updated_fields = [],
    update_io_logs_pk_list = []):

    if not item_list:
        StockIOLog.objects.only('pk').filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization_id=org_id,
            purchase__is_queueing_order=is_queueing_order,
            purchase__id=cart_instance_id
        ).update(status=Status.INACTIVE)

    for cart_item in item_list:
        try:
            existing_log = StockIOLog.objects.only(*io_log_updated_fields).get(
                status=Status.DISTRIBUTOR_ORDER,
                organization_id=org_id,
                stock__id=cart_item.get('stock_id'),
                purchase__is_queueing_order=is_queueing_order,
                purchase__id=cart_instance_id,
            )
            existing_log.__dict__.update(**cart_item)
            update_cart_item_instances.append(existing_log)
            update_io_logs_pk_list.append(existing_log.pk)
        except (StockIOLog.DoesNotExist):
            create_cart_item_instances.append(StockIOLog(
                organization_id=org_id,
                entry_by_id=entry_by_id,
                **cart_item
            ))
        except (StockIOLog.MultipleObjectsReturned):
            existing_log = StockIOLog.objects.only(*io_log_updated_fields).filter(
                status=Status.DISTRIBUTOR_ORDER,
                organization_id=org_id,
                stock__id=cart_item.get('stock_id'),
                purchase__is_queueing_order=is_queueing_order,
                purchase__id=cart_instance_id
            ).first()
            existing_log.__dict__.update(**cart_item)
            update_cart_item_instances.append(existing_log)
            update_io_logs_pk_list.append(existing_log.pk)

            item_pks = StockIOLog.objects.only(*io_log_updated_fields).filter(
                status=Status.DISTRIBUTOR_ORDER,
                organization_id=org_id,
                stock__id=cart_item.get('stock_id'),
                purchase__is_queueing_order=is_queueing_order,
                purchase__id=cart_instance_id
            ).values_list('pk', flat=True)
            pk_list = list(item_pks[1:])
            StockIOLog.objects.filter(pk__in=pk_list).update(status=Status.INACTIVE)
    return update_cart_item_instances, create_cart_item_instances, update_io_logs_pk_list

def update_cart_v2(
    org_id,
    user_id,
    cart_group = None,
    cart = True,
    order_id = None,
    clear_cart = True,):

    DATE_FORMAT = '%Y-%m-%d'
    _date_now = datetime.strptime(
        time.strftime(DATE_FORMAT, time.localtime()), DATE_FORMAT).date()

    org = Organization.objects.only('id').get(pk=org_id)

    try:
        setting = Organization.objects.only('id').get(
            pk=303
        ).get_settings()
    except Organization.DoesNotExist:
        setting = Organization.objects.only('id').get(
            pk=41
        ).get_settings()

    cart_group_id = cart_group if cart_group else org.get_or_add_cart_group(only_fields=['id'], set_cache=True)
    queueing_cart_instance_id = get_or_create_cart_instance(org_id, setting.organization_id, cart_group_id, user_id, True, True)
    regular_cart_instance_id = get_or_create_cart_instance(org_id, setting.organization_id, cart_group_id, user_id, False, True)
    queueing_cart_total_amount = 0
    queueing_cart_total_discount = 0
    regular_cart_total_amount = 0
    regular_cart_total_discount = 0

    regular_cart_items = []
    queueing_cart_items = []
    io_log_updated_fields = [
        'date',
        'rate',
        'quantity',
        'discount_rate',
        'discount_total',
        'purchase_id',
        'status',
        'round_discount',
    ]

    update_io_logs_pk_list = []
    aggregated_cart_items = []

    if not cart and order_id:
        if clear_cart:
            aggregated_cart_items = list(StockIOLog.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                purchase__id=order_id
            ).exclude(status=Status.INACTIVE).values('stock_id').order_by().annotate(
                total_quantity = Coalesce(Sum('quantity'), 0.00)
            ))

        else:
            aggregated_cart_items = list(StockIOLog.objects.filter(
                Q(purchase__id=order_id) |
                Q(purchase__distributor_order_group__id=cart_group_id),
                status=Status.DISTRIBUTOR_ORDER,
            ).exclude(status=Status.INACTIVE).values('stock_id').order_by().annotate(
                total_quantity = Coalesce(Sum('quantity'), 0.00)
            ))
    else:
        aggregated_cart_items = list(StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            purchase__distributor_order_group__id=cart_group_id
        ).exclude(status=Status.INACTIVE).values('stock_id').order_by().annotate(
            total_quantity=Coalesce(Sum('quantity'), 0.00)
        ))

    for item in aggregated_cart_items:
        stock = Stock.objects.only(
            'product_id',
            'orderable_stock',
        ).get(pk=item['stock_id'])
        product = Product.objects.only(
            'order_mode',
            'is_queueing_item',
            'trading_price',
            'discount_rate',
            'primary_unit_id',
            'secondary_unit_id',
            'conversion_factor',
            'order_limit_per_day',
        ).get(pk=stock.product_id)

        if setting.overwrite_order_mode_by_product:
            product_order_mode = product.order_mode
        else:
            product_order_mode = setting.allow_order_from

        if product_order_mode == AllowOrderFrom.OPEN:
            total_qty = calculate_total_quantity_based_on_various_criteria(product, item, user_id)

            discount_total = (total_qty * (product.trading_price or 0) * (product.discount_rate or 0)) / 100
            if total_qty > 0:
                io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': total_qty,
                    'rate': product.trading_price or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': product.discount_rate or 0,
                    'discount_total': discount_total,
                    'conversion_factor': product.conversion_factor,
                    'purchase_id': regular_cart_instance_id
                }
                regular_cart_total_amount += io_item.get('rate', 0) * io_item.get('quantity', 0)
                regular_cart_total_discount += io_item.get('discount_total', 0)
                regular_cart_items.append(io_item)
        elif product_order_mode == AllowOrderFrom.STOCK:
            total_qty = calculate_total_quantity_based_on_various_criteria(product, item, user_id)

            if stock.orderable_stock >= total_qty:
                stock_updated_qty = total_qty
            elif total_qty > stock.orderable_stock > 0:
                stock_updated_qty = stock.orderable_stock
            else:
                stock_updated_qty = 0

            discount_total = (stock_updated_qty * (product.trading_price or 0) * (product.discount_rate or 0)) / 100
            if stock_updated_qty > 0:
                io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': stock_updated_qty,
                    'rate': product.trading_price or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': product.discount_rate or 0,
                    'discount_total': discount_total,
                    'purchase_id': regular_cart_instance_id,
                    'conversion_factor': product.conversion_factor,
                }
                regular_cart_total_amount += io_item.get('rate', 0) * io_item.get('quantity', 0)
                regular_cart_total_discount += io_item.get('discount_total', 0)
                regular_cart_items.append(io_item)
        else:
            total_qty = calculate_total_quantity_based_on_various_criteria(product, item, user_id)

            if stock.orderable_stock >= total_qty:
                _updated_qty = total_qty
            elif total_qty > stock.orderable_stock > 0:
                _updated_qty = stock.orderable_stock
            else:
                _updated_qty = 0

            queueing_qty =  total_qty - _updated_qty
            discount_total = (_updated_qty * (product.trading_price or 0) * (product.discount_rate or 0)) / 100
            if _updated_qty > 0:
                io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': _updated_qty,
                    'rate': product.trading_price or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': product.discount_rate or 0,
                    'discount_total': discount_total,
                    'conversion_factor': product.conversion_factor,
                    'purchase_id': regular_cart_instance_id
                }
                regular_cart_total_amount += io_item.get('rate', 0) * io_item.get('quantity', 0)
                regular_cart_total_discount += io_item.get('discount_total', 0)
                regular_cart_items.append(io_item)
            if queueing_qty > 0:
                _discount_total = (queueing_qty * (product.trading_price or 0) * (product.discount_rate or 0)) / 100
                queueing_io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': queueing_qty,
                    'rate': product.trading_price or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': product.discount_rate or 0,
                    'discount_total': _discount_total,
                    'conversion_factor': product.conversion_factor,
                    'purchase_id': queueing_cart_instance_id
                }
                queueing_cart_total_discount
                queueing_cart_total_amount += queueing_io_item.get('rate', 0) * queueing_io_item.get('quantity', 0)
                queueing_cart_total_discount += queueing_io_item.get('discount_total', 0)
                queueing_cart_items.append(queueing_io_item)

    regular_cart_total_amount = float(format(regular_cart_total_amount, '.3f'))
    regular_cart_total_discount = float(format(regular_cart_total_discount, '.3f'))
    regular_cart_grand_total = regular_cart_total_amount - regular_cart_total_discount
    regular_cart_round = float(format(round(regular_cart_grand_total) - regular_cart_grand_total, '.3f'))
    regular_cart_items = distribute_round_among_cart_items(
        regular_cart_items,
        regular_cart_grand_total,
        regular_cart_round,
    )
    regular_cart_grand_total = regular_cart_grand_total + regular_cart_round

    queueing_cart_total_amount = float(format(queueing_cart_total_amount, '.3f'))
    queueing_cart_total_discount = float(format(queueing_cart_total_discount, '.3f'))
    queueing_cart_grand_total = queueing_cart_total_amount - queueing_cart_total_discount
    queueing_cart_round = float(format(round(queueing_cart_grand_total) - queueing_cart_grand_total, '.3f'))
    queueing_cart_items = distribute_round_among_cart_items(
        queueing_cart_items,
        queueing_cart_grand_total,
        queueing_cart_round,
    )
    queueing_cart_grand_total = queueing_cart_grand_total + queueing_cart_round

    update_cart_item_instances = []
    create_cart_item_instances = []
    update_cart_item_instances, create_cart_item_instances, update_io_logs_pk_list = update_or_create(
        regular_cart_items,
        update_cart_item_instances,
        create_cart_item_instances,
        org_id,
        regular_cart_instance_id,
        user_id,
        False,
        io_log_updated_fields,
        update_io_logs_pk_list,
    )
    update_cart_item_instances, create_cart_item_instances, update_io_logs_pk_list = update_or_create(
        queueing_cart_items,
        update_cart_item_instances,
        create_cart_item_instances,
        org_id,
        queueing_cart_instance_id,
        user_id,
        True,
        io_log_updated_fields,
        update_io_logs_pk_list,
    )
    # Inactive pks that's not available for stock or daily limit
    if update_io_logs_pk_list:
        removable_ios = StockIOLog.objects.only('pk').filter(
            status=Status.DISTRIBUTOR_ORDER,
            purchase__distributor_order_group__id=cart_group_id
        ).exclude(pk__in=update_io_logs_pk_list)
        removable_ios.update(status=Status.INACTIVE)

    StockIOLog.objects.bulk_create(create_cart_item_instances)
    StockIOLog.objects.bulk_update(
        update_cart_item_instances,
        io_log_updated_fields,
        batch_size=10
    )

    regular_cart_instance = Purchase.objects.only(
        'amount',
        'discount',
        'round_discount',
        'grand_total',
    ).get(pk=regular_cart_instance_id)

    regular_cart_instance.amount = regular_cart_total_amount
    regular_cart_instance.discount = regular_cart_total_discount
    regular_cart_instance.round_discount = regular_cart_round
    regular_cart_instance.grand_total = regular_cart_grand_total

    queueing_cart_instance = Purchase.objects.only(
        'amount',
        'discount',
        'round_discount',
        'grand_total',
    ).get(pk=queueing_cart_instance_id)
    queueing_cart_instance.amount = queueing_cart_total_amount
    queueing_cart_instance.discount = queueing_cart_total_discount
    queueing_cart_instance.round_discount = queueing_cart_round
    queueing_cart_instance.grand_total = queueing_cart_grand_total

    Purchase.objects.bulk_update(
        [regular_cart_instance, queueing_cart_instance],
        ['amount', 'discount', 'round_discount', 'grand_total'],
        batch_size=5
    )
    cart_group = DistributorOrderGroup.objects.only(
        'sub_total',
        'discount',
        'round_discount',
    ).get(pk=cart_group_id)

    cart_group.sub_total = regular_cart_total_amount + queueing_cart_total_amount
    cart_group.discount = regular_cart_total_discount + queueing_cart_total_discount
    cart_group.round_discount = regular_cart_round + queueing_cart_round
    DistributorOrderGroup.objects.bulk_update(
        [cart_group],
        ['sub_total', 'round_discount', 'discount',],
        batch_size=1
    )
