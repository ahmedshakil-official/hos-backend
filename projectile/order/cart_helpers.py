import decimal

from django.db import transaction
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from versatileimagefield.serializers import VersatileImageFieldSerializer

from common.enums import Status
from common.healthos_helpers import CustomerHelper, HealthOSHelper

from core.enums import AllowOrderFrom

from order.models import Cart, CartItem
from order.utils import (
    prepare_product_for_cart,
    get_delivery_hub_wise_total_quantity,
    get_round_discount_amount_for_cart_item,
    calculate_regular_total_quantity_based_on_various_criteria,
    calculate_queueing_total_quantity_based_on_various_criteria
)

from pharmacy.models import Stock
from pharmacy.utils import get_tentative_delivery_date


healthos_helper = HealthOSHelper()


def get_user_carts(user):
    current_datetime = timezone.now()

    # get or create the user's regular cart object
    regular_cart, _ = Cart.objects.get_or_create(
        user_id=user.id,
        organization_id=user.organization_id,
        status=Status.ACTIVE,
        is_pre_order=False,
        defaults={
            "date": current_datetime.date(),
            "delivery_date": get_tentative_delivery_date(current_datetime),
        },
    )

    # get or create the user's pre-order cart object
    pre_order_cart, _ = Cart.objects.get_or_create(
        user_id=user.id,
        organization_id=user.organization_id,
        status=Status.ACTIVE,
        is_pre_order=True,
        defaults={
            "date": current_datetime.date(),
            "delivery_date": get_tentative_delivery_date(
                order_date=current_datetime, is_queueing_order=True
            ),
        },
    )

    return regular_cart, pre_order_cart


def get_custom_round(value):
    # Convert the value to a floating-point number if it's a string
    if isinstance(value, str):
        value = float(value)

    # Split the value into integer and decimal parts
    integer_part, decimal_part = divmod(value, 1)

    # Determine the rounding direction based on the decimal part
    if decimal_part < 0.5:
        round_amount = -decimal_part
    else:
        round_amount = 1 - decimal_part

    return round_amount


def calculate_cart_total(cart):
    calculated_total = (
        CartItem()
        .get_all_actives()
        .filter(cart_id=cart.id)
        .aggregate(
            grand_total=Coalesce(Sum("total_amount"), Value(decimal.Decimal("0.00"))),
            discount=Coalesce(Sum("discount_amount"), Value(decimal.Decimal("0.00"))),
        )
    )

    cart_round_amount = get_custom_round(
        calculated_total.get("discount", decimal.Decimal("0.00"))
    )

    cart.sub_total = calculated_total.get(
        "grand_total", decimal.Decimal("0.00")
    ) + calculated_total.get("discount", decimal.Decimal("0.00"))
    cart.discount = calculated_total.get("discount", decimal.Decimal("0.00"))
    cart.round = cart_round_amount
    cart.grand_total = (
        calculated_total.get("grand_total", decimal.Decimal("0.00")) - cart_round_amount
    )
    # Update the cart delivery date
    current_datetime = timezone.now()
    # get the delivery date
    delivery_date = get_tentative_delivery_date(
        current_datetime, is_queueing_order=cart.is_pre_order
    )
    cart.delivery_date = delivery_date
    # Update the cart amounts and delivery date
    cart.save(update_fields=["sub_total", "discount", "round", "grand_total", "delivery_date"])


@transaction.atomic
def update_cart_v2(cart_products, user):

    customer_helper = CustomerHelper(organization_id=user.organization.id)
    customer_cumulative_discount_factor = float(customer_helper.get_cumulative_discount_factor())

    stock_quantity_dict = {
        item["stock"]: item["quantity"] for item in cart_products
    }

    stock_ids = list(stock_quantity_dict.keys())
    # Fetch all relevant stocks in a single query
    stocks = (
        Stock()
        .get_all_actives()
        .filter(id__in=stock_ids)
        .select_related(
            "product",
            "product__manufacturing_company",
        )
        .only(
            "id",
            "alias",
            "stock",
            "product__trading_price",
            "product__full_name",
            "product__is_published",
            "product__is_salesable",
            "product__discount_rate",
            "product__is_queueing_item",
            "product__order_mode",
            "product__order_limit_per_day",
            "product__order_limit_per_day_mirpur",
            "product__order_limit_per_day_uttara",
            "product__image",
            "product__manufacturing_company__name",
            "product__minimum_order_quantity",
        )
    )

    regular_cart, pre_order_cart = get_user_carts(user=user)

    items_to_be_removed = []

    cart_items_to_create = []
    cart_items_to_update = []

    # Get all existing cart items for the regular and pre-order carts
    existing_cart_items = (
        CartItem()
        .get_all_actives()
        .filter(
            Q(cart_id=regular_cart.id)
            | Q(cart_id=pre_order_cart.id),
            stock_id__in=stock_ids,
        )
    )

    # Create a dictionary to map existing cart items to their stock IDs
    existing_cart_items_dict = {
        (cart_item.cart_id, cart_item.stock_id): cart_item
        for cart_item in existing_cart_items
    }

    for stock in stocks:
        product = stock.product
        product_price = product.trading_price
        product_quantity = stock_quantity_dict.get(stock.id, 0)
        discount_per_product = (product_price * product.discount_rate) / 100

        if not product.is_queueing_item:
            cart_type = regular_cart
        elif product.is_queueing_item:
            cart_type = pre_order_cart

        # retrieving currently we accepting order base on product order mode or not
        setting = healthos_helper.settings()
        # Check if the order mode is set globally or product wise
        if setting.overwrite_order_mode_by_product:
            product_order_mode = product.order_mode
        else:
            product_order_mode = setting.allow_order_from

        if AllowOrderFrom.STOCK_AND_NEXT_DAY != product_order_mode:
            quantity = calculate_regular_total_quantity_based_on_various_criteria(
                product=product,
                quantity=product_quantity,
                user_id=user.id,
                orderable_stock=stock.orderable_stock,
                product_order_mode=product_order_mode
            )

            discount_amount = get_round_discount_amount_for_cart_item(
                user=user,
                product=product,
                quantity=quantity
            )
            total_amount = round((product_price * quantity) - discount_amount)
            product_discount_rate = product.discount_rate or 0
            final_discount_rate = product_discount_rate + float(customer_cumulative_discount_factor)

            cart_item_data = {
                "cart_id": cart_type.id,
                "stock_id": stock.id,
                "stock_alias": stock.alias,
                "organization_id": user.organization_id,
                "product_name": product.full_name,
                "quantity": quantity,
                "discount_rate": final_discount_rate,
                "discount_amount": discount_amount,
                "total_amount": total_amount,
                "mrp": product_price,
                "price": product_price - discount_per_product,
                "company_name": product.manufacturing_company.name,
                "entry_by_id": user.id,
                "status": Status.ACTIVE,
            }

        # Try to get an existing cart item for the same stock in the same cart
        existing_cart_item = existing_cart_items_dict.get((cart_type.id, stock.id))

        if product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY:
            q_updated_quantity = 0
            if existing_cart_item:
                try:
                    pre_order_cart_item = existing_cart_items_dict.get((pre_order_cart.id, stock.id))
                    regular_cart_item = existing_cart_items_dict.get((regular_cart.id, stock.id))
                    existing_quantity_in_cart_quantity = regular_cart_item.quantity + pre_order_cart_item.quantity
                except AttributeError:
                    # if product is pre order and order_able_stock is 0 then product will
                    # be add in pre_order no regular order. in this case we need to get quantity of pre_order
                    if not product.is_queueing_item:
                        existing_quantity_in_cart_quantity = regular_cart_item.quantity
                    else:
                        existing_quantity_in_cart_quantity = pre_order_cart_item.quantity
                # check if cart quantity has changed
                q_updated_quantity = (
                    product_quantity - existing_quantity_in_cart_quantity
                )

            quantity = calculate_regular_total_quantity_based_on_various_criteria(
                product=product,
                user_id=user.id,
                quantity=product_quantity,
                changed_quantity=q_updated_quantity,
                orderable_stock=stock.orderable_stock,
                product_order_mode=product_order_mode
            )

            if stock.orderable_stock >= quantity:
                _updated_qty = quantity
            elif quantity > stock.orderable_stock > 0:
                _updated_qty = stock.orderable_stock
            else:
                _updated_qty = 0

            queueing_qty = calculate_queueing_total_quantity_based_on_various_criteria(
                product=product,
                stock=stock,
                quantity=product_quantity,
                changed_quantity=q_updated_quantity,
                _updated_qty=_updated_qty,
                product_order_mode=product_order_mode
            )

            if _updated_qty >= 0:
                discount_amount = get_round_discount_amount_for_cart_item(
                    user=user,
                    product=product,
                    quantity=_updated_qty
                )
                product_discount_rate = product.discount_rate or 0
                final_discount_rate = product_discount_rate + float(customer_cumulative_discount_factor)
                total_amount = round((product_price * _updated_qty) - discount_amount)
                existing_cart_item = existing_cart_items_dict.get((regular_cart.id, stock.id))

                prepare_product_for_cart(
                    cart_type=regular_cart,
                    stock=stock,
                    user=user,
                    product=product,
                    quantity=_updated_qty,
                    final_discount_rate=final_discount_rate,
                    discount_amount=discount_amount,
                    total_amount=total_amount,
                    product_price=product_price,
                    discount_per_product=discount_per_product,
                    existing_cart_item=existing_cart_item,
                    product_quantity=product_quantity
                )
            if queueing_qty >= 0:
                discount_amount = get_round_discount_amount_for_cart_item(
                    user=user,
                    product=product,
                    quantity=queueing_qty
                )
                product_discount_rate = product.discount_rate or 0
                final_discount_rate = product_discount_rate + float(customer_cumulative_discount_factor)
                total_amount = round((product_price * queueing_qty) - discount_amount)
                existing_cart_item = existing_cart_items_dict.get((pre_order_cart.id, stock.id))

                prepare_product_for_cart(
                    cart_type=pre_order_cart,
                    stock=stock,
                    user=user,
                    product=product,
                    quantity=queueing_qty,
                    final_discount_rate=final_discount_rate,
                    discount_amount=discount_amount,
                    total_amount=total_amount,
                    product_price=product_price,
                    discount_per_product=discount_per_product,
                    existing_cart_item=existing_cart_item,
                    product_quantity=product_quantity
                )

        if existing_cart_item and product_order_mode != AllowOrderFrom.STOCK_AND_NEXT_DAY:
            # check if cart quantity has changed
            updated_quantity = (
                product_quantity - existing_cart_item.quantity
            )
            quantity = calculate_regular_total_quantity_based_on_various_criteria(
                product=product,
                user_id=user.id,
                quantity=product_quantity,
                changed_quantity=updated_quantity,
                orderable_stock=stock.orderable_stock,
                product_order_mode=product_order_mode
            )
            # Update existing cart item if it already exists
            existing_cart_item.quantity = quantity
            existing_cart_item.discount_amount = discount_amount
            existing_cart_item.total_amount = total_amount
            cart_items_to_update.append(existing_cart_item)

            if product_quantity < 1 or not product.is_salesable or not product.is_published or quantity < 1:
                items_to_be_removed.append(existing_cart_item.id)

        elif product_quantity > 0 and product.is_published and product.is_salesable and product_order_mode != AllowOrderFrom.STOCK_AND_NEXT_DAY:
            # Append to the list of cart items to create
            cart_items_to_create.append(CartItem(**cart_item_data))


    # Use bulk_create to insert all new cart items in a single query
    if cart_items_to_create:
        CartItem.objects.bulk_create(cart_items_to_create)
    # Use bulk_update to update existing cart items in a single query
    if cart_items_to_update:
        CartItem.objects.bulk_update(
            cart_items_to_update, fields=["quantity", "discount_amount", "total_amount"]
        )

    if items_to_be_removed:
        # Remove cart items from the cart
        CartItem.objects.filter(id__in=items_to_be_removed).update(status=Status.INACTIVE)

    # Calculate regular cart sub total
    calculate_cart_total(regular_cart)

    # Calculate pre-order cart sub total
    calculate_cart_total(pre_order_cart)

    # return regular_cart
    return {
        "regular_cart": regular_cart,
        "pre_order_cart": pre_order_cart,
    }
