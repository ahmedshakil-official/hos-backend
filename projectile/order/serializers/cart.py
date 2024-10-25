"""Serializer for Cart Models."""

from core.custom_serializer.organization import OrganizationModelSerializer

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from order.models import Cart

from .cart_items import CartItemModelSerializer


class CartMeta(ListSerializer.Meta):
    model = Cart
    fields = ListSerializer.Meta.fields + (
        "is_pre_order",
        "sub_total",
        "discount",
        "round",
        "grand_total",
        "status",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()


class CartModelSerializer:
    class List(ListSerializer):
        organization = OrganizationModelSerializer.LiteWithMinOrderAmount()
        cart_items = CartItemModelSerializer.List(read_only=True, many=True)

        class Meta(CartMeta):
            fields = CartMeta.fields + (
                "date",
                "delivery_date",
                "user",
                "organization",
                "cart_items",
                "discount_info",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()
