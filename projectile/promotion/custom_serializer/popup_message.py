
from rest_framework.serializers import ValidationError
from versatileimagefield.serializers import VersatileImageFieldSerializer
from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from common.validators import validate_unique_name
from ..models import PopUpMessage


class PopUpMessageMeta(ListSerializer.Meta):
    model = PopUpMessage

    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class PopUpMessageModelSerializer:

    class List(ListSerializer):
        image = VersatileImageFieldSerializer(
            sizes="banner_images",
            required=False
        )

        class Meta(PopUpMessageMeta):
            fields = PopUpMessageMeta.fields + (
                'status',
                'is_removable',
                'message',
                'image',
                'url',
                'is_public',
                'is_published',
                'first_published_date',
                'last_unpublished_date'
            )

        def validate_message(self, value):
            if validate_unique_name(self, value, PopUpMessage, 'message'):
                return value
            else:
                raise ValidationError(
                    'THERE_IS_ALREADY_AN_POPUP_MESSAGE_WITH_SAME_TEXT')
