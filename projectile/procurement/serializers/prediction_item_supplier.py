from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from core.serializers import (
    PersonOrganizationLiteSerializer,
)

from ..models import PredictionItemSupplier

class PredictionItemSupplierMeta(ListSerializer.Meta):
    model = PredictionItemSupplier
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'rate',
        'quantity',
        'priority',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class PredictionItemSupplierModelSerializer:

    class List(ListSerializer):
        # supplier = PersonOrganizationLiteSerializer(
        #     read_only=True,
        #     allow_null=True,
        #     fields=('id', 'alias', 'company_name', 'phone',)
        # )

        class Meta(PredictionItemSupplierMeta):
            fields = PredictionItemSupplierMeta.fields + (
                # 'supplier',
            )
            read_only_fields = PredictionItemSupplierMeta.read_only_fields + ()

    class ListWithSupplier(ListSerializer):
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'phone',)
        )

        class Meta(PredictionItemSupplierMeta):
            fields = PredictionItemSupplierMeta.fields + (
                'supplier',
            )
            read_only_fields = PredictionItemSupplierMeta.read_only_fields + ()
