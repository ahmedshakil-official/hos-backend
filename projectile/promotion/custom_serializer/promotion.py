from rest_framework.serializers import ValidationError
from rest_framework.serializers import (
    ModelSerializer, ImageField,
)
from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from common.validators import validate_unique_name
from ..models import Promotion

class PromotionMeta(ListSerializer.Meta):
    model = Promotion

    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class PromotionModelSerializer:

    class Mini(ModelSerializer):

        class Meta(PromotionMeta):
            fields = (
                'id',
                'message',
                'image'
            )

    class List(ListSerializer):
        image = ImageField(required=False)

        class Meta(PromotionMeta):
            fields = PromotionMeta.fields + (
                'status',
                'message',
                'image',
            )

        # def validate_message(self, value):
        #     if validate_unique_name(self, value, Promotion, 'message'):
        #         return value
        #     else:
        #         raise ValidationError(
        #             'THERE_IS_ALREADY_AN_PROMOTION_WITH_SAME_MESSAGE')
