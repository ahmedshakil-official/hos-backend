from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext as _

from common.choices import WriteChoices
from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer
from common.enums import Status
from core.custom_serializer.organization import OrganizationModelSerializer
from ecommerce.models import WishlistItem, Wishlist
from pharmacy.custom_serializer.stock import DistributorSalesableStock
from pharmacy.helpers import get_product_short_name


class WishlistItemMeta(ListSerializer.Meta):
    model = WishlistItem
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class WishlistItemModelSerializer:
    class List(ListSerializer):
        stock = DistributorSalesableStock.Details()
        organization = OrganizationModelSerializer.Lite()

        class Meta(WishlistItemMeta):
            fields = WishlistItemMeta.fields + (
                'created_at',
                'organization',
                'product_name',
                'stock',
                'suggested_price',
                'sell_quantity_per_week',
            )

    class Post(ListSerializer):
        type = serializers.ChoiceField(choices=WriteChoices, write_only=True)

        class Meta(WishlistItemMeta):
            fields = WishlistItemMeta.fields + (
                'stock',
                'type',
                'suggested_price',
                'sell_quantity_per_week',
            )

        def validate_stock(self, value):
            choice = self.context['request'].data.get('type')
            if choice == WriteChoices.POST and WishlistItem.objects.filter(
                    wishlist__organization_id=self.context['request'].user.organization.id,
                    stock=value,
                    status=Status.ACTIVE,
            ).exists():
                error = {
                    'detail': _('THIS_PRODUCT_IS_ALREADY_IN_YOUR_WISHLIST')
                }
                raise ValidationError(error)
            return value

        @transaction.atomic
        def create(self, validated_data):
            try:
                choice = validated_data['type']
                org_id = self.context['request'].user.organization.id
                if choice == WriteChoices.POST:
                    wishlist_item = WishlistItem.objects.create(
                        wishlist=Wishlist.objects.get_or_create(
                            organization_id=org_id,
                        )[0],
                        organization_id=org_id,
                        stock_id=validated_data['stock'].id,
                        product_name=get_product_short_name(validated_data['stock'].product),
                        suggested_price=validated_data.get('suggested_price', 0),
                        sell_quantity_per_week=validated_data.get('sell_quantity_per_week', 0),
                        entry_by_id=self.context['request'].user.id,
                    )
                    wishlist_item.wishlist.update_wishlist_item_count()
                    return wishlist_item
                elif choice == WriteChoices.DELETE:
                    wishlist_item = WishlistItem.objects.select_for_update().get(
                        wishlist__organization__id=org_id,
                        stock_id=validated_data['stock'].id,
                        status=Status.ACTIVE,
                    )
                    wishlist_item.status = Status.INACTIVE
                    wishlist_item.save()
                    wishlist_item.wishlist.update_wishlist_item_count()
                    return wishlist_item
            except Exception as ObjectDoesNotExist:
                raise ValidationError(ObjectDoesNotExist)

            return validated_data
