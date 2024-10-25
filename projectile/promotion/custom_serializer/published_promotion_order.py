from rest_framework.serializers import (
    ValidationError,
)
from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)
from common.enums import Status
from core.custom_serializer.organization import (
    OrganizationModelSerializer,
)
from .published_promotion import PublishedPromotionModelSerializer
from ..models import PublishedPromotionOrder

class PublishedPromotionOrderMeta(ListSerializer.Meta):
    model = PublishedPromotionOrder

    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class PublishedPromotionOrderModelSerializer:

    class Basic(ListSerializer):

        class Meta(PublishedPromotionOrderMeta):
            fields = PublishedPromotionOrderMeta.fields + (
                'published_promotion',
                'quantity',
                'amount',
                'date',
                'contact_no',
            )

        def validate_published_promotion(self, value):
            request = self.context.get('request')
            organization = request.user.organization
            # Check organization already claimed this offer or not
            queryset = PublishedPromotionOrder.objects.filter(
                status=Status.ACTIVE,
                organization=organization,
                published_promotion=value
            )
            if not queryset.exists():
                return value
            raise ValidationError("YOU_HAVE_ALREADY_CLAIMED_THIS_OFFER")


    class List(ListSerializer):
        published_promotion = PublishedPromotionModelSerializer.List()
        organization = OrganizationModelSerializer.Lite()

        class Meta(PublishedPromotionOrderMeta):
            fields = PublishedPromotionOrderMeta.fields + (
                'organization',
                'published_promotion',
                'quantity',
                'amount',
                'date',
                'contact_no',
            )
