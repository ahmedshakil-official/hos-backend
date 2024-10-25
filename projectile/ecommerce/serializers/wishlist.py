from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer
from common.enums import Status

from core.custom_serializer.organization import OrganizationModelSerializer
from ecommerce.models import Wishlist
from ecommerce.serializers.wishlist_item import WishlistItemModelSerializer


class WishlistMeta(ListSerializer.Meta):
    model = Wishlist
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class WishlistModelSerializer:
    class Lite(ListSerializer):
        organization = OrganizationModelSerializer.Lite()

        class Meta(WishlistMeta):
            fields = WishlistMeta.fields + (
                'organization',
                'total_item'
            )

    class List(ListSerializer):
        organization = OrganizationModelSerializer.Lite()
        wishlist_items = serializers.SerializerMethodField()

        def get_wishlist_items(self, obj):
            return WishlistItemModelSerializer.List(obj.wishlist_items.filter(status=Status.ACTIVE), many=True).data

        class Meta(WishlistMeta):
            fields = WishlistMeta.fields + (
                'organization',
                'total_item',
                'wishlist_items',
            )
