from django.db import transaction
from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status
from core.serializers import (
    PersonOrganizationLiteSerializer,
)

from ..models import PredictionItemMark
from .prediction_item import PredictionItemModelSerializer
from ..enums import PredictionItemMarkType

class PredictionItemMarkMeta(ListSerializer.Meta):
    model = PredictionItemMark
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class PredictionItemMarkModelSerializer:

    class List(ListSerializer):
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'phone',)
        )
        employee = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'first_name', 'last_name', 'phone',)
        )

        class Meta(PredictionItemMarkMeta):
            fields = PredictionItemMarkMeta.fields + (
                'rate',
                'supplier',
                'employee',
                'type',
                'remarks',
                'created_at',
            )
            read_only_fields = PredictionItemMarkMeta.read_only_fields + ()


    class Post(ListSerializer):

        def validate_prediction_item(self, value):
            _type = self.initial_data.get('type')
            request = self.context.get('request')

            data = PredictionItemMark.objects.filter(
                status=Status.ACTIVE,
                organization__id=request.user.organization_id,
                prediction_item=value,
                type=_type,
            )

            if data.exists() and _type == str(PredictionItemMarkType.MARK):
                raise serializers.ValidationError(
                    'This item already marked.'
                )
            elif data.exists() and _type == str(PredictionItemMarkType.UN_MARK):
                raise serializers.ValidationError(
                    'This item already unmarked.'
                )
            return value

        class Meta(PredictionItemMarkMeta):
            fields = PredictionItemMarkMeta.fields + (
                'prediction_item',
                'rate',
                'supplier',
                'employee',
                'type',
                'remarks',
            )
            read_only_fields = PredictionItemMarkMeta.read_only_fields + ()
