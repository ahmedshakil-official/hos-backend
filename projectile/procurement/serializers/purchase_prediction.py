from django.db import transaction
from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status
from core.models import ScriptFileStorage
from core.enums import FilePurposes


from ..models import PurchasePrediction

class PurchasePredictionMeta(ListSerializer.Meta):
    model = PurchasePrediction
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'date',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class PurchasePredictionModelSerializer:

    class List(ListSerializer):

        class Meta(PurchasePredictionMeta):
            fields = PurchasePredictionMeta.fields + (
                'label',
                'prediction_file',
                'is_locked',
            )
            read_only_fields =PurchasePredictionMeta.read_only_fields + ()


    class PopulateDataFromPredFile(serializers.Serializer):
        file = serializers.PrimaryKeyRelatedField(
            queryset=ScriptFileStorage.objects.filter(
                status=Status.ACTIVE,
                file_purpose=FilePurposes.PURCHASE_PREDICTION
            ),
            required=True
        )


    class LockUpdateSerializer(ListSerializer):
        class Meta(PurchasePredictionMeta):
            fields = ("is_locked",)
