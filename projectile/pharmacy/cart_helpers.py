from datetime import datetime
import time, os, logging
import pandas as pd
from copy import deepcopy
from dotmap import DotMap
from django.db.models.functions import Coalesce
from django.db.models import Sum, Q

from common.enums import Status
from common.utils import get_item_from_list_of_dict
from common.healthos_helpers import HealthOSHelper, CustomerHelper
from core.enums import AllowOrderFrom
from pharmacy.enums import StockIOType
from pharmacy.utils import (
    get_or_set_min_order_amount_in_cache,
    get_or_create_cart_instance,
    get_delivery_date_for_product,
    get_cart_group_id, calculate_queueing_quantity_based_on_various_criteria,
    get_product_dynamic_discount_rate,
)

from pharmacy.models import Stock, StockIOLog, Product, Purchase, DistributorOrderGroup

logger = logging.getLogger(__name__)

heathos_helper = HealthOSHelper()

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

    # If no io_items data passed all old should should be inactive
    if not item_list:
        ios_to_be_removed = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization_id=org_id,
            # purchase__is_queueing_order=is_queueing_order,
            purchase_id=cart_instance_id
        )
        if ios_to_be_removed.exists():
            ios_to_be_removed.update(status=Status.INACTIVE)
    for cart_item in item_list:
        try:
            existing_log = StockIOLog.objects.only(*io_log_updated_fields).get(
                status=Status.DISTRIBUTOR_ORDER,
                organization_id=org_id,
                stock_id=cart_item.get('stock_id'),
                # purchase__is_queueing_order=is_queueing_order,
                purchase_id=cart_instance_id,
            )
            existing_log.__dict__.update(**cart_item)
            update_cart_item_instances.append(existing_log)
            update_io_logs_pk_list.append(existing_log.pk)
        except StockIOLog.DoesNotExist:
            create_cart_item_instances.append(StockIOLog(
                organization_id=org_id,
                entry_by_id=entry_by_id,
                **cart_item
            ))
        except StockIOLog.MultipleObjectsReturned:
            existing_log = StockIOLog.objects.only(*io_log_updated_fields).filter(
                status=Status.DISTRIBUTOR_ORDER,
                organization_id=org_id,
                stock_id=cart_item.get('stock_id'),
                # purchase__is_queueing_order=is_queueing_order,
                purchase_id=cart_instance_id
            ).first()
            existing_log.__dict__.update(**cart_item)
            update_cart_item_instances.append(existing_log)
            update_io_logs_pk_list.append(existing_log.pk)

            item_pks = StockIOLog.objects.only(*io_log_updated_fields).filter(
                status=Status.DISTRIBUTOR_ORDER,
                organization_id=org_id,
                stock_id=cart_item.get('stock_id'),
                # purchase__is_queueing_order=is_queueing_order,
                purchase_id=cart_instance_id
            ).values_list('pk', flat=True)
            pk_list = list(item_pks[1:])
            StockIOLog.objects.filter(pk__in=pk_list).update(status=Status.INACTIVE)
    return update_cart_item_instances, create_cart_item_instances, update_io_logs_pk_list

def prepare_delivery_coupon_io_item(cart_instance_id):
    """Prepare io log(StockIOLogs) data for delivery coupon

    Args:
        cart_instance_id (int): purchase instance id for regular or pre order
    Return:
        type (int): data for creating StockIOLogs instance of delivery coupon
    """
    coupon_stock = heathos_helper.get_delivery_coupon_stock_data()
    if coupon_stock:
        DATE_FORMAT = "%Y-%m-%d"
        _date_now = datetime.strptime(
            time.strftime(DATE_FORMAT, time.localtime()),
            DATE_FORMAT
        ).date()
        product = coupon_stock.product
        total_qty = 1
        discount_total = (total_qty * (product.trading_price or 0) * (product.discount_rate or 0)) / 100
        # Get primary unit id or None
        try:
            primary_unit_id = product.primary_unit.id
            secondary_unit_id = product.secondary_unit.id
        except Exception as _e:
            primary_unit_id = None
            secondary_unit_id = None

        io_item = {
            'status': Status.DISTRIBUTOR_ORDER,
            'stock_id': coupon_stock.id,
            'quantity': total_qty,
            'rate': product.trading_price or 0,
            'batch': 'N/A',
            'date': _date_now,
            'primary_unit_id': primary_unit_id,
            'secondary_unit_id': secondary_unit_id,
            'discount_rate': product.discount_rate or 0,
            'discount_total': discount_total,
            'conversion_factor': product.conversion_factor,
            'purchase_id': cart_instance_id,
            'type': StockIOType.OUT,
        }
        return io_item
    return None


def update_cart(
    org_id,
    user_id,
    new_cart_items = None,
    cart = True,
    order_id = None,
    clear_cart = True):
    """_summary_

    Args:
        org_id (int): Organization id from the user who is sending the request
        user_id (int): the user is sending the request
        new_cart_items (list, optional): new cart items as a list, it's the stock_io_logs part of the payload
        cart (bool, optional): define if it's a cart or a reorder. Defaults to True.
        order_id (int, optional): the order id, required for re order
        clear_cart (bool, optional): Define if the existing cart will be cleared for re order not just append with exiting items
    """
    DATE_FORMAT = "%Y-%m-%d"
    _date_now = datetime.strptime(
        time.strftime(DATE_FORMAT, time.localtime()),
        DATE_FORMAT
    ).date()
    setting = heathos_helper.settings()
    org_min_order_amount = get_or_set_min_order_amount_in_cache(org_id=org_id)
    # Customer org helper
    customer_helper = CustomerHelper(org_id)
    existing_regular_order_amount = customer_helper.get_non_group_total_amount_for_regular_order()
    existing_pre_order_amount = customer_helper.get_non_group_total_amount_for_pre_order()
    is_coupon_already_available_for_regular_order = customer_helper.get_delivery_coupon_availability_for_regular_order()
    is_coupon_already_available_for_pre_order = customer_helper.get_delivery_coupon_availability_for_pre_order()

    """Get cart group id, cart group is defining a group of cart(Purchase) instance for a specific organization,
        An organization can only have one cart group"""
    cart_group_id = get_cart_group_id(org_id)
    # Get the pre order cart instance(Purchase) id from cache or db
    queueing_cart_instance_id = get_or_create_cart_instance(
        org_id,
        setting.organization_id,
        cart_group_id,
        user_id,
        True,
        True,
    )
    # Get the regular order cart instance(Purchase) id from cache or db
    regular_cart_instance_id = get_or_create_cart_instance(
        org_id,
        setting.organization_id,
        cart_group_id,
        user_id,
        False,
        True,
    )
    queueing_cart_total_amount = 0
    queueing_cart_total_discount = 0
    queueing_cart_total_discount_considering_base_discount = 0
    regular_cart_total_amount = 0
    regular_cart_total_discount = 0
    regular_cart_total_discount_considering_base_discount = 0

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

    delete_logs_pk_list = []
    aggregated_cart_items = []
    update_io_logs_pk_list = []
    cart_instance_id_list = [queueing_cart_instance_id, regular_cart_instance_id]

    if not cart and order_id:
        if clear_cart:
            aggregated_cart_items = list(StockIOLog.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                purchase__id=order_id
            ).values('stock_id').order_by().annotate(
                total_quantity = Coalesce(Sum('quantity'), 0.00)
            ))

        else:
            cart_instance_id_list.append(order_id)
            aggregated_cart_items = list(StockIOLog.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                purchase__id__in=cart_instance_id_list
            ).values('stock_id').order_by().annotate(
                total_quantity = Coalesce(Sum('quantity'), 0.00)
            ))
    else:
        # Get the aggregated qty for all cart items(Both regular and pre order)
        # Finally merge new items and existing items
        aggregated_cart_items = list(StockIOLog.objects.filter(
            organization__id=org_id,
            status=Status.DISTRIBUTOR_ORDER,
            purchase__id__in=cart_instance_id_list
        ).values("stock_id", "quantity").order_by())
        data_df = pd.DataFrame(aggregated_cart_items)
        new_items_df = pd.DataFrame(new_cart_items, columns=["stock", "quantity"])
        new_items_df.rename(columns={"stock": "stock_id", "quantity": "total_quantity"}, inplace=True)
        if not data_df.empty:
            # Remove Delivery Coupon as we will add it later based on order amount and min order maount
            # data_df = data_df.drop(data_df[data_df["stock_id"] == heathos_helper.get_delivery_coupon_stock_id()].index, axis=0)
            data_df = data_df.groupby(["stock_id"], as_index=False).sum()
            data_df = data_df.rename(columns={"quantity": "total_quantity",})
        if not new_items_df.empty and not data_df.empty:
            final_df = pd.merge(data_df, new_items_df, on='stock_id', how='outer', suffixes=('_df1', '_df2'))
            final_df['total_quantity_df2'].fillna(final_df['total_quantity_df1'], inplace=True)
            final_df.drop(['total_quantity_df1'], axis=1, inplace=True)
            final_df.rename(columns={"total_quantity_df2": "total_quantity"}, inplace=True)
            # Find changes of qty
            final_df['change'] = final_df["total_quantity"] - data_df["total_quantity"]
            final_df['change'].fillna(final_df["total_quantity"], inplace=True)
            aggregated_cart_items =  final_df.to_dict("records")
        elif not new_items_df.empty and data_df.empty:
            # As no existing items available to new items qty will be the change
            new_items_df['change'] = new_items_df["total_quantity"]
            aggregated_cart_items =  new_items_df.to_dict("records")
        elif new_items_df.empty and not data_df.empty:
            # As no new items added there will be no change
            data_df['change'] = 0
            aggregated_cart_items =  data_df.to_dict("records")
        else:
            aggregated_cart_items = []
    # For the property 'change', negative value = decrease, positive = increase, 0 = no change
    stock_id_list = list(map(lambda item: item['stock_id'], aggregated_cart_items))
    stocks_queryset_list = list(Stock.objects.filter(pk__in=stock_id_list).only(
        'id',
        'product_id',
        'orderable_stock',
    ).values(
        'id',
        'product_id',
        'orderable_stock',
    ).order_by())
    product_id_list = list(map(lambda item: item['product_id'], stocks_queryset_list))
    product_queryset_list = list(Product.objects.filter(pk__in=product_id_list).only(
        'id',
        'order_mode',
        'is_queueing_item',
        'trading_price',
        'discount_rate',
        'primary_unit_id',
        'secondary_unit_id',
        'conversion_factor',
        'order_limit_per_day',
        'order_limit_per_day_mirpur',
        'order_limit_per_day_uttara',
        'minimum_order_quantity',
    ).values(
        'id',
        'order_mode',
        'is_queueing_item',
        'trading_price',
        'discount_rate',
        'primary_unit_id',
        'secondary_unit_id',
        'conversion_factor',
        'order_limit_per_day',
        'order_limit_per_day_mirpur',
        'order_limit_per_day_uttara',
        'minimum_order_quantity',
    ))
    # Get customer cumulative dynamic discount
    # customer_cumulative_discount_factor = float(customer_helper.get_cumulative_discount_factor())
    # Prepare payload based on current stock, order mode, delivery hub etc.
    for item in aggregated_cart_items:
        stock = DotMap(get_item_from_list_of_dict(stocks_queryset_list, 'id', item['stock_id']))
        product = DotMap(get_item_from_list_of_dict(product_queryset_list, 'id', stock.product_id))
        # Get dynamic discount rate
        final_discount_rate = float(get_product_dynamic_discount_rate(
            user_org_id=org_id,
            trading_price=product.trading_price,
            discount_rate=product.discount_rate,
            stock_id=item['stock_id']
        ))

        # Check if the order mode is set globally or product wise
        if setting.overwrite_order_mode_by_product:
            product_order_mode = product.order_mode
        else:
            # Use the global order mode setting for all products
            product_order_mode = setting.allow_order_from
            # If the global order mode allows ordering from both stock and open orders
            if setting.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN:
                product_order_mode = product.order_mode
                 # If the product's order mode is set to allow ordering from stock and next day
                if product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY:
                    # Adjust the product's order mode to only allow ordering from stock
                    product_order_mode = AllowOrderFrom.STOCK

        # If Product order mode is open, it will always go to regular items
        if product_order_mode == AllowOrderFrom.OPEN:
            total_qty = calculate_total_quantity_based_on_various_criteria(
                product, item, user_id, stock.orderable_stock, product_order_mode
            )
            # final_discount_rate = (product.discount_rate or 0) + customer_cumulative_discount_factor
            discount_total = (
                total_qty * (product.trading_price or 0) * final_discount_rate
            ) / 100
            base_discount_total = (
                total_qty * (product.trading_price or 0) * (product.discount_rate or 0)
            ) / 100
            if total_qty > 0:
                io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': total_qty,
                    'rate': product.trading_price or 0,
                    'base_discount': product.discount_rate or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': final_discount_rate,
                    'discount_total': discount_total,
                    'conversion_factor': product.conversion_factor,
                    'purchase_id': regular_cart_instance_id,
                    'type': StockIOType.INPUT,
                }
                regular_cart_total_amount += io_item.get('rate', 0) * io_item.get('quantity', 0)
                regular_cart_total_discount += io_item.get('discount_total', 0)
                regular_cart_total_discount_considering_base_discount += base_discount_total
                regular_cart_items.append(io_item)
        elif product_order_mode == AllowOrderFrom.STOCK:
            # If Order model is Stock max qty will be current orderable stock
            total_qty = calculate_total_quantity_based_on_various_criteria(
                product, item, user_id, stock.orderable_stock, product_order_mode
            )

            if stock.orderable_stock >= total_qty:
                stock_updated_qty = total_qty
            elif total_qty > stock.orderable_stock > 0:
                stock_updated_qty = stock.orderable_stock
            else:
                stock_updated_qty = 0
            # final_discount_rate = (product.discount_rate or 0) + customer_cumulative_discount_factor
            discount_total = (
                stock_updated_qty * (product.trading_price or 0) * final_discount_rate
            ) / 100
            base_discount_total = (
                stock_updated_qty * (product.trading_price or 0) * (product.discount_rate or 0)
            ) / 100
            if stock_updated_qty > 0:
                io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': stock_updated_qty,
                    'rate': product.trading_price or 0,
                    'base_discount': product.discount_rate or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': final_discount_rate,
                    'discount_total': discount_total,
                    'purchase_id': regular_cart_instance_id,
                    'conversion_factor': product.conversion_factor,
                    'type': StockIOType.INPUT,
                }
                regular_cart_total_amount += io_item.get('rate', 0) * io_item.get('quantity', 0)
                regular_cart_total_discount += io_item.get('discount_total', 0)
                regular_cart_total_discount_considering_base_discount += base_discount_total
                regular_cart_items.append(io_item)
        else:
            # If order mode is Stock and Next day, we need to decide how much qty will go to regular vs pre order
            total_qty = calculate_total_quantity_based_on_various_criteria(
                product,
                item,
                user_id,
                stock.orderable_stock,
                product_order_mode
            )

            if stock.orderable_stock >= total_qty:
                _updated_qty = total_qty
            elif total_qty > stock.orderable_stock > 0:
                _updated_qty = stock.orderable_stock
            else:
                _updated_qty = 0

            queueing_qty = calculate_queueing_quantity_based_on_various_criteria(
                item=item,
                _updated_qty=_updated_qty,
                product=product,
                stock=stock,
                product_order_mode=product_order_mode
            )
            # final_discount_rate = (product.discount_rate or 0) + customer_cumulative_discount_factor
            discount_total = (
                _updated_qty * (product.trading_price or 0) * final_discount_rate
            ) / 100
            base_discount_total = (
                _updated_qty * (product.trading_price or 0) * (product.discount_rate or 0)
            ) / 100
            # Regular order part
            if _updated_qty > 0:
                io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': _updated_qty,
                    'rate': product.trading_price or 0,
                    'base_discount': product.discount_rate or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': final_discount_rate,
                    'discount_total': discount_total,
                    'conversion_factor': product.conversion_factor,
                    'purchase_id': regular_cart_instance_id,
                    'type': StockIOType.INPUT,
                }
                regular_cart_total_amount += io_item.get('rate', 0) * io_item.get('quantity', 0)
                regular_cart_total_discount += io_item.get('discount_total', 0)
                regular_cart_total_discount_considering_base_discount += base_discount_total
                regular_cart_items.append(io_item)
            # Pre order Part
            if queueing_qty > 0:
                # final_discount_rate = (product.discount_rate or 0) + customer_cumulative_discount_factor
                _discount_total = (
                    queueing_qty * (product.trading_price or 0) * final_discount_rate
                ) / 100
                base_discount_total = (
                    queueing_qty * (product.trading_price or 0) * (product.discount_rate or 0)
                ) / 100
                queueing_io_item = {
                    'status': Status.DISTRIBUTOR_ORDER,
                    'stock_id': item['stock_id'],
                    'quantity': queueing_qty,
                    'rate': product.trading_price or 0,
                    'base_discount': product.discount_rate or 0,
                    'batch': 'N/A',
                    'date': _date_now,
                    'primary_unit_id': product.primary_unit_id,
                    'secondary_unit_id': product.secondary_unit_id,
                    'discount_rate': final_discount_rate,
                    'discount_total': _discount_total,
                    'conversion_factor': product.conversion_factor,
                    'purchase_id': queueing_cart_instance_id,
                    'type': StockIOType.INPUT,
                }
                queueing_cart_total_amount += queueing_io_item.get('rate', 0) * queueing_io_item.get('quantity', 0)
                queueing_cart_total_discount += queueing_io_item.get('discount_total', 0)
                queueing_cart_total_discount_considering_base_discount += base_discount_total
                queueing_cart_items.append(queueing_io_item)

    regular_cart_total_amount = float(format(regular_cart_total_amount, '.3f'))
    regular_cart_total_discount = float(format(regular_cart_total_discount, '.3f'))
    regular_cart_total_discount_considering_base_discount = float(
        format(regular_cart_total_discount_considering_base_discount, '.3f')
    )
    regular_cart_grand_total = round((regular_cart_total_amount - regular_cart_total_discount), 3)
    regular_cart_grand_total_considering_base_discount = round(
        (regular_cart_total_amount - regular_cart_total_discount_considering_base_discount), 3
    )
    regular_cart_round = float(
        format(round(regular_cart_grand_total) - regular_cart_grand_total, '.3f')
    )
    regular_cart_round_considering_base_discount = float(
        format(
            round(regular_cart_grand_total_considering_base_discount) -
            regular_cart_grand_total_considering_base_discount, '.3f'
        )
    )
    regular_cart_items = distribute_round_among_cart_items(
        regular_cart_items,
        regular_cart_grand_total,
        regular_cart_round,
    )
    regular_cart_grand_total = regular_cart_grand_total + regular_cart_round
    regular_cart_grand_total_considering_base_discount = regular_cart_grand_total_considering_base_discount + regular_cart_round_considering_base_discount

    queueing_cart_total_amount = float(format(queueing_cart_total_amount, '.3f'))
    queueing_cart_total_discount = float(format(queueing_cart_total_discount, '.3f'))
    queueing_cart_total_discount_considering_base_discount = float(
        format(queueing_cart_total_discount_considering_base_discount, '.3f')
    )
    queueing_cart_grand_total = round((queueing_cart_total_amount - queueing_cart_total_discount), 3)
    queueing_cart_grand_total_considering_base_discount = round(
        (queueing_cart_total_amount - queueing_cart_total_discount_considering_base_discount), 3
    )
    queueing_cart_round = float(format(round(queueing_cart_grand_total) - queueing_cart_grand_total, '.3f'))
    queueing_cart_round_considering_base_discount = float(
        format(
            round(queueing_cart_grand_total_considering_base_discount) -
            queueing_cart_grand_total_considering_base_discount, '.3f'
        )
    )
    queueing_cart_items = distribute_round_among_cart_items(
        queueing_cart_items,
        queueing_cart_grand_total,
        queueing_cart_round,
    )
    queueing_cart_grand_total = queueing_cart_grand_total + queueing_cart_round
    queueing_cart_grand_total_considering_base_discount = queueing_cart_grand_total_considering_base_discount + queueing_cart_round_considering_base_discount
    # Check if delivery coupon needed to be added or not based on org min_order_amount and exiting order amount
    # should_add_delivery_coupon_for_regular_order = (
    #     regular_cart_grand_total + existing_regular_order_amount < org_min_order_amount and
    #     regular_cart_items and
    #     not is_coupon_already_available_for_regular_order
    # )
    should_add_delivery_coupon_for_regular_order = False
    # should_add_delivery_coupon_for_pre_order = (
    #     queueing_cart_grand_total + existing_pre_order_amount < org_min_order_amount and
    #     queueing_cart_items and
    #     not is_coupon_already_available_for_pre_order
    # )
    should_add_delivery_coupon_for_pre_order = False
    if should_add_delivery_coupon_for_regular_order:
        coupon_io_for_regular_order = prepare_delivery_coupon_io_item(regular_cart_instance_id)
        regular_cart_items.append(coupon_io_for_regular_order)
        # Add delivery coupon price with regular order amount
        coupon_price = coupon_io_for_regular_order.get("rate", 0)
        regular_cart_total_amount += coupon_price
        regular_cart_grand_total += coupon_price

    if should_add_delivery_coupon_for_pre_order:
        coupon_io_for_pre_order = prepare_delivery_coupon_io_item(queueing_cart_instance_id)
        queueing_cart_items.append(coupon_io_for_pre_order)
        # Add delivery coupon price with pre order amount
        coupon_price = coupon_io_for_pre_order.get("rate", 0)
        queueing_cart_total_amount += coupon_price
        queueing_cart_grand_total += coupon_price

    update_cart_item_instances = []
    create_cart_item_instances = []
    io_item_entry_by_id = user_id
    # Create or update the items as StockIOLOg
    update_cart_item_instances, create_cart_item_instances, update_io_logs_pk_list = update_or_create(
        regular_cart_items,
        update_cart_item_instances,
        create_cart_item_instances,
        org_id,
        regular_cart_instance_id,
        io_item_entry_by_id,
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
        io_item_entry_by_id,
        True,
        io_log_updated_fields,
        update_io_logs_pk_list,
    )

    # Inactive pks that's not available for stock or daily limit
    if update_io_logs_pk_list:
        removable_ios = StockIOLog.objects.only('pk').filter(
            status=Status.DISTRIBUTOR_ORDER,
            # purchase__distributor_order_group__id=cart_group.id
            purchase__pk__in=[regular_cart_instance_id, queueing_cart_instance_id],
        ).exclude(pk__in=update_io_logs_pk_list)
        removable_ios.update(status=Status.INACTIVE)

    # Hit the DB
    StockIOLog.objects.bulk_create(create_cart_item_instances)
    StockIOLog.objects.bulk_update(
        update_cart_item_instances,
        io_log_updated_fields,
        batch_size=10
    )
    # Get current dynamic discount factor
    dynamic_discount_factor = customer_helper.get_organization_and_area_discount()
    org_discount_factor = dynamic_discount_factor.get("organization_discount_factor", 0.00)
    area_discount_factor = dynamic_discount_factor.get("area_discount_factor", 0.00)
    # Get delivery date for regular order cart instance
    regular_tentative_delivery_date = get_delivery_date_for_product(is_queueing_item=False)
    regular_dynamic_discount_amount = regular_cart_grand_total_considering_base_discount - regular_cart_grand_total
    # Update the regular cart data
    Purchase.objects.filter(
        pk=regular_cart_instance_id,
    ).update(
        amount=regular_cart_total_amount,
        discount=regular_cart_total_discount,
        round_discount=regular_cart_round,
        grand_total=regular_cart_grand_total,
        tentative_delivery_date=regular_tentative_delivery_date,
        dynamic_discount_amount=regular_dynamic_discount_amount,
        customer_dynamic_discount_factor=org_discount_factor,
        customer_area_dynamic_discount_factor=area_discount_factor
    )

    # Get delivery date for pre order cart instance
    queueing_tentative_delivery_date = get_delivery_date_for_product(is_queueing_item=True)
    queueing_dynamic_discount_amount = queueing_cart_grand_total_considering_base_discount - queueing_cart_grand_total
    # Update pre order cart data
    Purchase.objects.filter(
        pk=queueing_cart_instance_id,
    ).update(
        amount=queueing_cart_total_amount,
        discount=queueing_cart_total_discount,
        round_discount=queueing_cart_round,
        grand_total=queueing_cart_grand_total,
        tentative_delivery_date=queueing_tentative_delivery_date,
        dynamic_discount_amount=queueing_dynamic_discount_amount,
        customer_dynamic_discount_factor=org_discount_factor,
        customer_area_dynamic_discount_factor=area_discount_factor
    )

    # Purchase.objects.bulk_update(
    #     [queueing_cart_instance],
    #     ['amount', 'discount', 'round_discount', 'grand_total', 'tentative_delivery_date'],
    #     batch_size=5
    # )
    # Update the cart group
    DistributorOrderGroup.objects.filter(pk=cart_group_id).update(
        sub_total=regular_cart_total_amount + queueing_cart_total_amount,
        discount=regular_cart_total_discount + queueing_cart_total_discount,
        round_discount=regular_cart_round + queueing_cart_round
    )

    # cart_group.sub_total = regular_cart_total_amount + queueing_cart_total_amount
    # cart_group.discount = regular_cart_total_discount + queueing_cart_total_discount
    # cart_group.round_discount = regular_cart_round + queueing_cart_round
    # cart_group.save(update_fields=['sub_total', 'round_discount', 'discount',])

    # Delete all previous io logs
    # if delete_logs_pk_list:
    #     delete_logs = StockIOLog.objects.filter(
    #         pk__in=delete_logs_pk_list
    #     ).only('pk')
    #     delete_logs._raw_delete(delete_logs.db)


def re_order(org_id, user_id, order_id, clear_cart):

    update_cart(
        org_id=org_id,
        user_id=user_id,
        cart=False,
        order_id=order_id,
        clear_cart=clear_cart
    )
