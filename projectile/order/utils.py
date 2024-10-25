import os
import decimal

from django.db import transaction
from django.utils import timezone
from django.db.models import Sum

from core.helpers import get_user_profile_details_from_cache
from core.enums import AllowOrderFrom
from common.enums import Status
from pharmacy.enums import PurchaseType, DistributorOrderType, StockIOType
from pharmacy.enums import (
    PurchaseType,
    DistributorOrderType,
    StockIOType,
    OrderTrackingStatus
)
from pharmacy.models import Purchase, StockIOLog, DistributorOrderGroup

DECIMAL_ZERO = decimal.Decimal("0.000")

def get_delivery_hub_wise_total_quantity(product, quantity, user_id):
    """returns total quantity by different delivery hub of a product"""

    total_quantity = quantity
    try:
        user_delivery_hub_short_code = get_user_profile_details_from_cache(
            user_id=user_id
        ).organization.delivery_hub.short_code


        # Check daily order limit
        if user_delivery_hub_short_code == "MH-1":
            if total_quantity >= product.order_limit_per_day_mirpur:
                total_quantity = product.order_limit_per_day_mirpur
        elif user_delivery_hub_short_code == "UH-1":
            if total_quantity >= product.order_limit_per_day_uttara:
                total_quantity = product.order_limit_per_day_uttara
        else:
            if total_quantity >= product.order_limit_per_day:
                total_quantity = product.order_limit_per_day
        return total_quantity

    except AttributeError:
        if total_quantity >= product.order_limit_per_day:
            total_quantity = product.order_limit_per_day

        return total_quantity


discount_rules = [
    {
        "min_amount": 2500,
        "discount": 1
    },
    {
        "min_amount": 5000,
        "discount": 1.15
    },
    {
        "min_amount": 10000,
        "discount": 1.25
    },
    {
        "min_amount": 15000,
        "discount": 1.50
    },
    {
        "min_amount": 20000,
        "discount": 1.75
    },
    {
        "min_amount": 30000,
        "discount": 2
    },

]


def get_discount_for_cart_and_order_items_v2(cart_grand_total, rounding_off=True):
    amount_to_reach_next_discount_level = 0
    current_discount_percentage = 0
    current_discount_amount = 0
    next_discount_percentage = 0
    next_discount_amount = 0
    for rule in discount_rules:
        if cart_grand_total >= rule["min_amount"]:
            current_discount_percentage = rule["discount"]
            current_discount_amount = (cart_grand_total * current_discount_percentage) / 100
            if rounding_off:
                current_discount_amount = round(current_discount_amount)
        else:
            amount_to_reach_next_discount_level = round(rule["min_amount"] - cart_grand_total)
            next_discount_percentage = rule["discount"]
            next_discount_amount = (rule["min_amount"] * next_discount_percentage) / 100
            if rounding_off:
                next_discount_amount = round(next_discount_amount)
            break
    return {
        "amount_to_reach_next_discount_level": amount_to_reach_next_discount_level,
        "current_discount_percentage": current_discount_percentage,
        "current_discount_amount": current_discount_amount,
        "next_discount_percentage": next_discount_percentage,
        "next_discount_amount": next_discount_amount
    }


# TODO: remove this method from pharmacy.utils once we replace cart v1 with v2
def calculate_queueing_total_quantity_based_on_various_criteria(
        quantity,
        _updated_qty,
        changed_quantity,
        product,
        stock,
        product_order_mode
):
    """
        Calculate the pre-order quantity based on various criteria including user input,
        updated quantity, product details, and stock availability.

        Parameters:
        - item (dict): A dictionary containing information about the item, including the total_quantity.
        - _updated_qty (int): The updated quantity for the item.
        - product (object): An object representing the product, with attributes such as minimum_order_quantity.
        - stock (object): An object representing the stock availability, with attributes like orderable_stock.
        - product_order_mode (enum- int): Represent current order mode of a product

        Returns:
        int: The calculated pre-order quantity based on the specified conditions.
    """
    # get user given order quantity
    given_qty = quantity or 0
    change = changed_quantity or 0
    is_decrement = change < 0
    # If orderable stock is less than MoQ it should only add regular item in cart at first request
    if (
        product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
        (0 < stock.orderable_stock <= _updated_qty or _updated_qty < stock.orderable_stock) and
        given_qty == 1
        ):
        return 0

    # get additional quantity which must be added in pre-order
    additional_qty = abs(given_qty - _updated_qty)

    # follow these below conditions,
    # if product.minimum_order_quantity is more than 1
    if product.minimum_order_quantity > 1:
        # if a user has regular quantity,
        # and additional_qty is more than 1 and less than product.minimum_order_quantity
        # then pre-order quantity should be 0
        if _updated_qty and 1 < additional_qty < product.minimum_order_quantity and is_decrement:
            queueing_qty = 0

        # if a user has regular quantity,
        # and additional_qty is not 0 and equal 1 and less than product.minimum_order_quantity
        # then pre-order quantity should be product.minimum_order_quantity
        elif (
            _updated_qty and
            0 != additional_qty < product.minimum_order_quantity
            ):
            queueing_qty = product.minimum_order_quantity

        # if a user has regular quantity,
        # and additional_qty is equal more than product.minimum_order_quantity,
        # then pre-order quantity should be additional_qty
        elif _updated_qty and additional_qty >= product.minimum_order_quantity:
            queueing_qty = additional_qty
        else:
            queueing_qty = 0
    else:
        queueing_qty = additional_qty

    # if product stock is 0,
    # then user given order quantity will be added in pre-order
    if stock.orderable_stock <= 0:

        # follow these below conditions,
        # if product.minimum_order_quantity is more than 1
        if product.minimum_order_quantity > 1:

            # if a user has regular quantity,
            # and additional_qty is more than 1 and less than product.minimum_order_quantity
            # then pre-order quantity should be 0
            if 1 < additional_qty < product.minimum_order_quantity and is_decrement:
                queueing_qty = 0

            # if a user has regular quantity,
            # and additional_qty is not 0 and equal 1 and less than product.minimum_order_quantity
            # then pre-order quantity should be product.minimum_order_quantity
            elif 0 != additional_qty < product.minimum_order_quantity:
                queueing_qty = product.minimum_order_quantity

            # if additional quantity is greater than product.minimum_order_quantity,
            # then queueing_qty should be value of additional quantity
            elif additional_qty >= product.minimum_order_quantity:
                queueing_qty = additional_qty
            else:
                queueing_qty = 0

        # if product.minimum_order_quantity is 1
        else:
            queueing_qty = additional_qty

    return queueing_qty



def calculate_regular_total_quantity_based_on_various_criteria(
        product,
        quantity,
        user_id,
        changed_quantity=None,
        orderable_stock=None,
        product_order_mode=None
):
    """
    Returns the total quantity for a product considering different delivery hubs.

    Parameters:
    - product (object): The product for which the total quantity is calculated.
    - item (dict): A dictionary containing item details, including 'total_quantity'.
    - User_id (int): The user's ID for fetching user-related information.

    Returns:
    - int: The total quantity based on the specified criteria, including order limits,
        minimum order quantity, and available stock for the given product.

    This function calculates the total quantity for a product based on various criteria
    such as minimum order quantity, available stock, and daily order limits.
    The result takes into account the user's delivery hub to apply hub-specific limits.
    """
    total_qty = quantity
    change = changed_quantity or 0
    is_decrement = change < 0

    try:
        user_delivery_hub_short_code = get_user_profile_details_from_cache(
            user_id=user_id
        ).organization.delivery_hub.short_code

        if product_order_mode != AllowOrderFrom.OPEN:

            # follow these below conditions,
            # if product.minimum_order_quantity is more than 1
            if product.minimum_order_quantity > 1:
                # Check if order quantity is greater than 1 and
                # less then minimum order quantity
                # then assign 0
                # Assume orderable stock is 3, moq 5 and order mode pre order in that case it should allow
                # Adding qty greater than 1 and less than min qty otherwise remove the item
                if (
                    1 < total_qty < product.minimum_order_quantity and
                    (
                        (
                            product_order_mode != AllowOrderFrom.STOCK_AND_NEXT_DAY and
                            total_qty > orderable_stock < product.minimum_order_quantity
                        ) or
                        (
                            product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
                            total_qty < orderable_stock
                        ) or
                        (
                            product_order_mode == AllowOrderFrom.STOCK and
                            total_qty < orderable_stock
                        )
                    ) and is_decrement
                    ):
                    total_qty = 0

                # Check if order quantity is not 0 and equal 1
                # then assign minimum_order_quantity in total_qty
                elif 0 != total_qty < product.minimum_order_quantity:
                    total_qty = product.minimum_order_quantity

            # Check order quantity not more than product stock
            if orderable_stock and total_qty > orderable_stock and orderable_stock > 0 and not is_decrement:
                total_qty = orderable_stock
        # If order mode is open allow any qty to add
        elif product_order_mode == AllowOrderFrom.OPEN and product.minimum_order_quantity > 1:
            # If qty is greater than one and smaller than MoQ
            if 1 < total_qty < product.minimum_order_quantity and is_decrement:
                total_qty = 0
            # Check if order quantity is not 0 and equal 1
            # then assign minimum_order_quantity in total_qty
            elif 0 != total_qty < product.minimum_order_quantity:
                total_qty = product.minimum_order_quantity


        # Check the daily order limit based on the user's delivery hub
        if user_delivery_hub_short_code == "MH-1":
            if total_qty >= product.order_limit_per_day_mirpur:
                total_qty = product.order_limit_per_day_mirpur
        elif user_delivery_hub_short_code == "UH-1":
            if total_qty >= product.order_limit_per_day_uttara:
                total_qty = product.order_limit_per_day_uttara
        else:
            if total_qty >= product.order_limit_per_day:
                total_qty = product.order_limit_per_day

        return total_qty

    except AttributeError:

        if product_order_mode != AllowOrderFrom.OPEN:
            # Check if order quantity is greater than 1 and
            # less then minimum order quantity
            # then assign 0
            # Assume orderable stock is 3, moq 5 and order mode pre order in that case it should allow
            # Adding qty greater than 1 and less than min qty otherwise remove the item
            if (
                1 < total_qty < product.minimum_order_quantity and
                (
                    (
                        product_order_mode != AllowOrderFrom.STOCK_AND_NEXT_DAY and
                        total_qty > orderable_stock < product.minimum_order_quantity
                    ) or
                    (
                        product_order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
                        total_qty < orderable_stock
                    ) or
                    (
                        product_order_mode == AllowOrderFrom.STOCK and
                        total_qty < orderable_stock
                    )
                ) and is_decrement
                ):
                total_qty = 0

            # Check if order quantity is not 0 or equal 1
            # then assign minimum_order_quantity in total_qty
            elif 0 != total_qty < product.minimum_order_quantity:
                total_qty = product.minimum_order_quantity

            # Check order quantity not more than product stock
            if orderable_stock and total_qty > orderable_stock and orderable_stock > 0:
                total_qty = orderable_stock

        # If order mode is open allow any qty to add
        elif product_order_mode == AllowOrderFrom.OPEN and product.minimum_order_quantity > 1:
            # If qty is greater than one and smaller than MoQ
            if 1 < total_qty < product.minimum_order_quantity and is_decrement:
                total_qty = 0
            # Check if order quantity is not 0 and equal 1
            # then assign minimum_order_quantity in total_qty
            elif 0 != total_qty < product.minimum_order_quantity:
                total_qty = product.minimum_order_quantity

        # Check order limit
        if total_qty >= product.order_limit_per_day:
            total_qty = product.order_limit_per_day

        return total_qty


def remove_discount_factor_for_coupon(request, data):
    """
    Removes the discount factor for a given coupon from the cumulative discount factor.

    Args:
    - request: The HTTP request object.
    - data: Dictionary containing the coupon ID information.

    Returns:
    - float: Updated discount factor after removing the coupon's discount factor or
            0.00 if the coupon ID matches the provided data.

    Note:
    - This function fetches the cumulative discount factor for a customer based on the organization ID
    from the request. If the provided coupon ID matches the 'EXPRESS_DELIVERY_STOCK_ID' from the environment,
    it returns 0.00, effectively removing the discount factor for that coupon. Otherwise, it returns
    the original discount rate factor for the customer.
    """

    # Importing necessary modules here to avoid circular import error
    from common.healthos_helpers import CustomerHelper

    # Fetch the cumulative discount factor for the customer's organization
    discount_rate_factor = CustomerHelper(
        request.user.organization_id
    ).get_cumulative_discount_factor()
    # Get the coupon ID from environment variables
    coupon = os.environ.get("EXPRESS_DELIVERY_STOCK_ID", None)
    # Check if the provided data's ID matches the coupon ID
    if str(data["id"]) == coupon:
        return 0.00  # If the coupon matches, remove the discount factor by returning 0.00
    else:
        return discount_rate_factor  # Otherwise, return the original discount factor


def get_cumulative_discount(organization_id, product):
    from common.healthos_helpers import CustomerHelper

    customer_helper = CustomerHelper(organization_id=organization_id)
    cumulative_discount_factor = customer_helper.get_cumulative_discount_factor()
    cumulative_discount = product.trading_price * (float(cumulative_discount_factor)/100)
    return cumulative_discount


def get_round_discount_amount_for_cart_item(user, product, quantity):
    discount_on_product = (product.trading_price * product.discount_rate) / 100
    cumulative_discount = get_cumulative_discount(
        organization_id=user.organization_id,
        product=product
    )
    discount = (discount_on_product  + cumulative_discount) * quantity
    return discount


def prepare_product_for_cart(
    cart_type,
    stock,
    user,
    product,
    quantity,
    final_discount_rate,
    discount_amount,
    total_amount,
    product_price,
    discount_per_product,
    product_quantity,
    existing_cart_item
):
    from common.enums import Status
    from order.models import CartItem

    cart_items_to_create = []
    cart_items_to_update = []
    items_to_be_removed = []

    cart_item_data = {}
    if not existing_cart_item and quantity != 0:
        mrp = product_price - discount_per_product
        price = product_price
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
                "mrp": mrp,
                "price": price,
                "company_name": product.manufacturing_company.name,
                "entry_by_id": user.id,
                "status": Status.ACTIVE,
            }

    if existing_cart_item:
            # Update existing cart item if it already exists
            existing_cart_item.quantity = quantity
            existing_cart_item.discount_amount = discount_amount
            existing_cart_item.total_amount = total_amount
            cart_items_to_update.append(existing_cart_item)

            if product_quantity < 1 or not product.is_salesable or not product.is_published or quantity < 1:
                items_to_be_removed.append(existing_cart_item.id)

    if product_quantity > 0 and product.is_published and product.is_salesable:
        # Append to the list of cart items to create
        cart_items_to_create.append(CartItem(**cart_item_data))

    # Use bulk_create to insert all new cart items in a single query
    if cart_items_to_create and not existing_cart_item and quantity != 0:
        CartItem.objects.bulk_create(cart_items_to_create)

    # Use bulk_update to update existing cart items in a single query
    if cart_items_to_update:
        CartItem.objects.bulk_update(
            cart_items_to_update, fields=["quantity", "discount_amount", "total_amount"]
        )

    # Remove cart items from the cart
    CartItem.objects.filter(id__in=items_to_be_removed).update(status=Status.INACTIVE)


    return True

@transaction.atomic
def clear_cart_v2(cart):
    """
    Clear the cart by resetting its values and marking associated CartItems as inactive.

    Args:
    - cart: Cart object to be cleared
    """
    from order.models import CartItem

    DECIMAL_ZERO = decimal.Decimal("0.000")

    # Reset cart values
    cart.grand_total = DECIMAL_ZERO
    cart.sub_total = DECIMAL_ZERO
    cart.discount = DECIMAL_ZERO
    cart.round = DECIMAL_ZERO

    # Save the updated cart with specific fields only
    cart.save(update_fields=["sub_total", "discount", "round", "grand_total"])

    # Mark all active CartItems related to the cart as inactive
    CartItem().get_all_actives().filter(cart_id=cart.id).update(status=Status.INACTIVE)


@transaction.atomic
def create_order_from_cart(organization_id:  int):
    """
    Create orders from carts based on the organization ID.

    Args:
    - organization_id: ID of the organization for which orders are created

    Returns:
    - List of created orders
    """
    from order.models import Cart, CartItem
    import uuid
    from pharmacy.models import OrderTracking

    distributor = os.environ.get("DISTRIBUTOR_ORG_ID", 303)
    orders = []
    stock_io_logs_to_create = []

    # Retrieve active carts associated with the organization ID
    carts = Cart().get_all_actives().filter(organization_id=organization_id).order_by("created_at")

    group_code = uuid.uuid4()
    for cart in carts:
        if cart.grand_total > 0:

            # Prepare order data using cart information
            # Create a DistributorOrderGroup to group orders related to the same organization
            distributor_order_group = DistributorOrderGroup.objects.create(
                organization_id=cart.organization_id,
                sub_total=float(cart.sub_total),
                discount=float(cart.discount),
                round_discount=float(cart.round * -1),
                order_type=DistributorOrderType.ORDER,
                group_id=group_code
            )

            current_order_status = OrderTrackingStatus.IN_QUEUE if cart.is_pre_order else OrderTrackingStatus.PENDING

            order_data = {
                "status": Status.DISTRIBUTOR_ORDER,
                "organization_id": cart.organization_id,
                "purchase_type": PurchaseType.VENDOR_ORDER,
                "purchase_date": timezone.now(),
                "distributor_id": distributor,
                "amount": round(cart.sub_total),
                "discount": float(cart.discount),
                "round_discount": float(cart.round * -1),
                "grand_total": round(cart.grand_total),
                "distributor_order_type": DistributorOrderType.ORDER,
                "tentative_delivery_date": cart.delivery_date,
                "is_queueing_order": cart.is_pre_order,
                "receiver_id": cart.user_id,
                "entry_by_id": cart.user_id,
                "current_order_status": current_order_status,
                "distributor_order_group": distributor_order_group
            }

            # Create a Purchase object (order) using the prepared order data
            order = Purchase.objects.create(**order_data)
            orders.append(order)

            OrderTracking.objects.create(
                order_id=order.id,
                entry_by_id=cart.user.id,
                order_status=current_order_status
            )

            # Retrieve cart items associated with the current cart
            cart_items = CartItem().get_all_actives().filter(cart_id=cart.id)

            # Create StockIOLog entries for each cart item
            for cart_item in cart_items:
                stock_io_logs_to_create.append(
                    StockIOLog(
                        purchase_id=order.id,
                        status=order.status,
                        organization_id=order.organization.id,
                        type=StockIOType.INPUT,
                        stock_id=cart_item.stock.id,
                        quantity=cart_item.quantity,
                        date=order.purchase_date,
                        discount_rate=cart_item.discount_rate,
                        discount_total=cart_item.discount_amount,
                        rate=cart_item.price,
                    )
                )

            # Clear the cart
            clear_cart_v2(cart)

    # Bulk create StockIOLog entries
    StockIOLog.objects.bulk_create(stock_io_logs_to_create)

    return orders


def get_user_carts(user):
    from common.enums import Status
    from order.models import Cart
    from pharmacy.utils import get_tentative_delivery_date

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


def cart_item_payload_for_user(user):
    """
    Retrieve aggregated cart item quantities for a specific user's carts.

    Args:
    - user: The user for whom to retrieve cart item data.

    Returns:
    - cart_products: A list of dictionaries containing aggregated cart
        item quantities in the format {'stock': str, 'quantity': int}.
    """

    from order.models import CartItem

    # Get regular and pre carts for the given user
    regular_cart, pre_cart = get_user_carts(user=user)

    # Retrieve aggregated cart item quantities for regular and pre carts
    cart_items = CartItem().get_all_actives().filter(
        cart_id__in=[regular_cart.id, pre_cart.id]
        ).values('stock_id').annotate(
            total_quantity=Sum('quantity')
        )

    # Create a list of dictionaries containing stock ID and total quantity
    cart_products = [
        {"stock": item['stock_id'], "quantity": item['total_quantity']}
        for item in cart_items
    ]

    return cart_products


# TODO: remove the function after a week of begin used in production
# to migrate cart v1 data to cart v2
def get_item_from_cart_v1(user, organization):
    """
    Retrieve cart items for a given user and organization.

    Args:
    - user_id (int): ID of the user.
    - organization_id (int): ID of the organization.

    Returns:
    - list: List of cart items with their quantities.
    """
    from django.core.cache import cache

    from pharmacy.models import StockIOLog
    from pharmacy.utils import get_or_create_cart_instance, get_cart_group_id

    from common.healthos_helpers import HealthOSHelper
    from common.cache_keys import CART_V1_DATA_RETRIEVE_KEY

    from order.cart_helpers import update_cart_v2

    # Initialize HealthOSHelper instance
    heathos_helper = HealthOSHelper()

    # Get settings from HealthOS
    setting = heathos_helper.settings()

    # Get cart group ID
    cart_group_id = get_cart_group_id(303)

    # Create or get queueing cart instance
    queueing_cart_instance_id = get_or_create_cart_instance(
        organization.id,
        setting.organization_id,
        cart_group_id,
        user.id,
        True,
        True,
    )

    # Create or get regular cart instance
    regular_cart_instance_id = get_or_create_cart_instance(
        organization.id,
        setting.organization_id,
        cart_group_id,
        user.id,
        False,
        True,
    )

    # Get cart items for cart instances from stock io log
    cart_items = StockIOLog.objects.filter(
        purchase__in=[queueing_cart_instance_id, regular_cart_instance_id],
        status=Status.DISTRIBUTOR_ORDER  # Assuming Status is defined elsewhere
    ).values("stock").annotate(
        quantity=Sum("quantity")
    )
    cart_products = list(cart_items)
    update_cart_v2(cart_products=cart_products, user=user)
    # set flag to cache to as cart item retrieved
    cache.set(
        key=f"{CART_V1_DATA_RETRIEVE_KEY}{organization.id}",
        value=True
    )
    return list(cart_items)
