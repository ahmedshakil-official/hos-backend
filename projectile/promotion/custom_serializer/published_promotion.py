from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)
from common .enums import Status
from core.custom_serializer.organization import (
    OrganizationModelSerializer,
)
from .promotion import PromotionModelSerializer
from ..models import PublishedPromotion

class PublishedPromotionMeta(ListSerializer.Meta):
    model = PublishedPromotion

    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class PublishedPromotionModelSerializer:

    class Mini(ListSerializer):

        class Meta(PublishedPromotionMeta):
            fields = PublishedPromotionMeta.fields + (
                'promotion',
            )

    class Basic(ListSerializer):

        class Meta(PublishedPromotionMeta):
            fields = PublishedPromotionMeta.fields + (
                'organization',
                'promotion',
            )

        def create(self, validated_data):
            promotion, created = PublishedPromotion.objects.get_or_create(
                status=Status.ACTIVE,
                **validated_data
            )
            if created:
                promotion.save()
            return promotion

    class List(ListSerializer):
        promotion = PromotionModelSerializer.Mini()
        organization = OrganizationModelSerializer.Lite()

        class Meta(PublishedPromotionMeta):
            fields = PublishedPromotionMeta.fields + (
                'status',
                'promotion',
                'organization',
            )
