"""Serializer for CartItem Models."""

from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from order.models import Cart, CartItem


class CartItemMeta(ListSerializer.Meta):
    model = CartItem
    fields = ListSerializer.Meta.fields + (
        "stock",
        "stock_alias",
        "product_name",
        "mrp",
        "price",
        "quantity",
        "discount_rate",
        "discount_amount",
        "total_amount",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()


class CartItemModelSerializer:
    class List(ListSerializer):
        class Meta(CartItemMeta):
            fields = CartItemMeta.fields + (
                "product_image",
                "company_name",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()
