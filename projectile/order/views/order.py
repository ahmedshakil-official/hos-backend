"""Views for Order"""
import datetime

from django.db.models import F, Sum, Prefetch
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response


from core.views.common_view import CreateAPICustomView
from core.enums import AllowOrderFrom
from core.helpers import get_user_profile_details_from_cache


from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsSalesman,
    AnyLoggedInUser,
    StaffIsProcurementOfficer,
)
from common.utils import get_healthos_settings
from common.enums import Status

from pharmacy.models import Stock, StockIOLog, Product
from pharmacy.enums import OrderTrackingStatus, DistributorOrderType

from validator_collection import checkers

from order.cart_helpers import update_cart_v2
from order.models import Cart, CartItem
from order.serializers.cart import CartModelSerializer
from order.serializers.order import OrderLiteSerializerV2
from order.utils import create_order_from_cart, cart_item_payload_for_user


class DistributorOrderPlaceV2(CreateAPICustomView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    queryset = Cart().get_all_actives()
    serializer_class = OrderLiteSerializerV2

    def post(self, request, *args, **kwargs):
        user = request.user
        organization_id = user.organization_id
        orders = create_order_from_cart(organization_id=organization_id)
        if len(orders)>0:
            serializer = OrderLiteSerializerV2(orders, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {"detail": "You have no item in the cart"},
            status=status.HTTP_200_OK,
        )


class DistributorOrderLimitPerDayV2(APIView):
    """Get order limit per day for product of a distributor"""
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )


    def get(self, request, *args, **kwargs):
        stock_alias = self.kwargs.get("alias", None)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_details = get_user_profile_details_from_cache(request.user.id)
        if checkers.is_uuid(stock_alias):
            stock_filter = { 'alias': stock_alias }
            stock_io_filter = { 'stock__alias': stock_alias }
        else:
            stock_filter = { 'id': stock_alias }
            stock_io_filter = { 'stock__id': stock_alias }
        stock = Stock.objects.only(
            'stock',
            'orderable_stock',
            'product',
            'organization'
        ).get(**stock_filter)
        distributor_settings = get_healthos_settings()
        product = Product.objects.values(
            'order_mode',
            'order_limit_per_day',
            'order_limit_per_day_mirpur',
            'order_limit_per_day_uttara',
            'is_queueing_item',
            'minimum_order_quantity',
        ).get(pk=stock.product_id)
        if distributor_settings.overwrite_order_mode_by_product:
            order_mode = product.get('order_mode')
        else:
            order_mode = distributor_settings.allow_order_from

        order_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id,
            date=current_date,
            **stock_io_filter
        ).exclude(
            purchase__current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
        ).values(
            'purchase__distributor_order_type'
        ).annotate(total_qty=Coalesce(Sum(F('quantity')), 0.00)).order_by()

        order_items_data = list(order_items)

        order_item = next(filter(lambda item: item['purchase__distributor_order_type'] == DistributorOrderType.ORDER, order_items_data), {})
        # cart_item = next(filter(lambda item: item['purchase__distributor_order_type'] == DistributorOrderType.CART, order_items_data), {})

        # as we have now cart v2 with different model we need to consider it too
        cart_v2_quantity = CartItem().get_all_actives().filter(
            stock_id=stock.id,
            organization_id=self.request.user.organization_id
        ).aggregate(
            total_quantity=Sum("quantity")
        )['total_quantity'] or 0

        try:
            # get order limit value based on delivery hub short_code
            short_code = user_details.organization.delivery_hub.short_code

            if short_code == "MH-1":
                order_limit = product.get("order_limit_per_day_mirpur")
            elif short_code == "UH-1":
                order_limit = product.get("order_limit_per_day_uttara")
            else:
                order_limit = product.get("order_limit_per_day")
        except AttributeError:
            order_limit = product.get("order_limit_per_day")

        limit_data = {
            "today": current_date,
            "order_quantity": order_item.get('total_qty', 0),
            "cart_quantity": cart_v2_quantity,
            "order_limit": order_limit,
            "allow_order_from": order_mode,
            "is_out_of_stock": stock.is_out_of_stock,
            "orderable_stock": stock.orderable_stock,
            "minimum_order_quantity": product.get("minimum_order_quantity", 1)

        }

        if order_mode == AllowOrderFrom.STOCK_AND_OPEN:
            order_mode = product.get('order_mode')
        if (
            (order_mode == AllowOrderFrom.OPEN) or
            (order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and product.get('is_queueing_item'))
            ):
            limit_data['rest_quantity'] = limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])
        elif (
            (order_mode == AllowOrderFrom.STOCK) or
            (order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and not product.get('is_queueing_item'))
            ):
            # limit_data['rest_quantity'] = min((limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])), (limit_data.get('orderable_stock') - (limit_data['order_quantity'] + limit_data['cart_quantity'])))
            limit_data['rest_quantity'] = min((limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])), (limit_data.get('orderable_stock') - (limit_data['cart_quantity'])))

        # if is_queueing_order == "false":
            # limit_data['rest_quantity'] = min((limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])), (limit_data.get('orderable_stock') - (limit_data['order_quantity'] + limit_data['cart_quantity'])))
            # limit_data['rest_quantity'] = min((limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])), (limit_data.get('orderable_stock') - (limit_data['cart_quantity'])))
        limit_data['add_to_queue'] = (order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and (limit_data.get("rest_quantity", 0) <= 0 or product.get('is_queueing_item')))
        return Response(limit_data, status=status.HTTP_200_OK)


class DistributorReOrderV2(CreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin
    )

    def get_queryset(self):
        cart_items = CartItem().get_all_actives()
        queryset = (
            Cart()
            .get_all_actives()
            .filter(user_id=self.request.user.id)
            .select_related(
                "organization",
            )
            .prefetch_related(Prefetch("cart_items", queryset=cart_items))
            .order_by("is_pre_order")
        )

        return queryset

    def post(self, request, *args, **kwargs):
        user = request.user
        order_id = self.request.data.get("order", None)
        is_clear = self.request.data.get("clear_cart", None)
        cart_products = []
        cart_item = cart_item_payload_for_user(user=user)
        if order_id:
            stock_item = StockIOLog.objects.filter(
                purchase_id=order_id
            ).values("stock", "quantity")
            cart_products = list(stock_item)
            stock_to_quantity = {
                product['stock']: product['quantity']
                for product in cart_products
            }
            new_cart_items = []
            for _item in cart_item:
                stock_value = _item.get('stock')
                if stock_value in stock_to_quantity:
                    _item['quantity'] += stock_to_quantity[stock_value]
                new_cart_items.append(_item)
            cart_products.extend(new_cart_items)
        if is_clear:
            # if clear cart true then we need to clear all the item from cart
            # creating dict map to compare stock id
            stock_to_quantity = {
                product['stock']: product['quantity']
                for product in cart_products
            }
            new_cart_items = []
            # if same item already exits in the cart then we need to update its
            # quantity with the given quantity other wise 2nd time cart quantity 0
            # will remove the item from cart
            for _item in cart_item:
                stock_value = _item.get('stock')
                if stock_value in stock_to_quantity:
                    _item['quantity'] = stock_to_quantity[stock_value]
                else:
                    _item['quantity'] = 0
                new_cart_items.append(_item)

            cart_products.extend(new_cart_items)
        update_cart_v2(cart_products=cart_products, user=user)

        response = CartModelSerializer.List(self.get_queryset(), many=True)
        return Response({"order_groups": response.data}, status=status.HTTP_201_CREATED)
