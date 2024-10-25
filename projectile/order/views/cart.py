"""Views for Cart"""

from django.db.models import Prefetch

from rest_framework import status
from rest_framework.response import Response

from core.views.common_view import ListCreateAPICustomView


from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsProcurementOfficer,
    StaffIsSalesman,
)

from order.cart_helpers import update_cart_v2
from order.models import Cart, CartItem
from order.utils import cart_item_payload_for_user, get_item_from_cart_v1

from order.serializers.cart import CartModelSerializer


class DistributorOrderCartListCreateV2(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = CartModelSerializer.List
    pagination_class = None

    def get_queryset(self):
        # for GET request get the cart v1 items
        # TODO: remove the after 1 month of
        from common.cache_keys import CART_V1_DATA_RETRIEVE_KEY
        from django.core.cache import cache

        is_retrieved = cache.get(
            key=f"{CART_V1_DATA_RETRIEVE_KEY}{self.request.user.organization.id}"
        )
        if not is_retrieved:
            get_item_from_cart_v1(
                user=self.request.user,
                organization=self.request.user.organization
            )
        # remove up till this comment line

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
        cart_products = request.data or []

        # for GET request get the cart v1 items
        # TODO: remove the after 1 month of
        from common.cache_keys import CART_V1_DATA_RETRIEVE_KEY
        from django.core.cache import cache

        is_retrieved = cache.get(
            key=f"{CART_V1_DATA_RETRIEVE_KEY}{self.request.user.organization.id}"
        )
        if not is_retrieved:
            get_item_from_cart_v1(
                user=self.request.user,
                organization=self.request.user.organization
            )
        # remove up till this comment line

        if cart_products:
            update_cart_v2(cart_products=cart_products, user=request.user)

            response = CartModelSerializer.List(self.get_queryset(), many=True)
            return Response({"order_groups": response.data}, status=status.HTTP_201_CREATED)
        else:
            # if post request with empty products information
            # we will generate a payload from existing item in cart
            # we need to check if cart item data has change or not while use was idle

            cart_products = cart_item_payload_for_user(
                user=self.request.user
            )

            update_cart_v2(cart_products=cart_products, user=request.user)
            response = CartModelSerializer.List(self.get_queryset(), many=True)
            return Response({"order_groups": response.data}, status=status.HTTP_201_CREATED)


    def list(self, request, *args, **kwargs):
        response_data = super().list(request, *args, **kwargs)

        # Transform the results into the expected structure
        transformed_results = {
            "order_groups": response_data.data
        }

        response_data.data = transformed_results
        return response_data
