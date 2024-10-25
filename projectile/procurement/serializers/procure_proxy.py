from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status, ActionType
from core.serializers import (
    PersonOrganizationLiteSerializer,
)

from ..models import Procure, ProcureItem


class ProcureProxyMeta(ListSerializer.Meta):
    model = Procure
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'date',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProcureModelProxySerializer:

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

        class Meta(ProcureProxyMeta):
            fields = ProcureProxyMeta.fields + (
                'supplier',
                'employee',
                'requisition',
                'sub_total',
                'discount',
                'operation_start',
                'operation_end',
                'remarks',
                'invoices',
                # 'geo_location_data',
            )
            read_only_fields = ProcureProxyMeta.read_only_fields + ()

    class ProductWiseReport(ListSerializer):
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

        class Meta(ProcureProxyMeta):
            fields = ProcureProxyMeta.fields + (
                'supplier',
                'employee',
            )
            read_only_fields = ProcureProxyMeta.read_only_fields + ()