from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from core.serializers import (
    PersonOrganizationLiteSerializer,
)

from ..models import ProcureIssueLog
from .prediction_item import PredictionItemModelSerializer

class ProcureIssueLogMeta(ListSerializer.Meta):
    model = ProcureIssueLog
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'date',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProcureIssueLogModelSerializer:

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
        prediction_item = PredictionItemModelSerializer.Lite()

        class Meta(ProcureIssueLogMeta):
            fields = ProcureIssueLogMeta.fields + (
                'supplier',
                'employee',
                'stock',
                'prediction_item',
                'type',
                'remarks',
                'prediction_item',
                # 'geo_location_data',
            )
            read_only_fields = ProcureIssueLogMeta.read_only_fields + ()


    class Post(ListSerializer):

        class Meta(ProcureIssueLogMeta):
            fields = ProcureIssueLogMeta.fields + (
                'supplier',
                'employee',
                'stock',
                'prediction_item',
                'type',
                'remarks',
                'geo_location_data',
            )
            read_only_fields = ProcureIssueLogMeta.read_only_fields + ()

    class Lite(ListSerializer):

        class Meta(ProcureIssueLogMeta):
            fields = ProcureIssueLogMeta.fields + (
                'supplier',
                'type',
                'remarks',
            )
            read_only_fields = ProcureIssueLogMeta.read_only_fields + ()
