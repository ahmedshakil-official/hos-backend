'''
Move following serializer on this page:
<class 'pharmacy.serializers.StockAdjustmentBasicSerializer'>
<class 'pharmacy.serializers.StockAdjustmentDetailsSerializer'>
<class 'pharmacy.serializers.StockAdjustmentSearchSerializer'>
<class 'pharmacy.serializers.StockAdjustmentSerializer'>
<class 'pharmacy.serializers.StockDisbursementListSerializer'>
'''

from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from core.custom_serializer.person_organization import (
    PersonOrganizationModelSerializer
)
from pharmacy.custom_serializer.store_point import (
    StorePointModelSerializer
)
from ..models import StockAdjustment

class StockAdjustmentMeta(ListSerializer):
    model = StockAdjustment
    fields = ListSerializer.Meta.fields + ()
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # we can add readonly field here
    )


class StockAdjustmentModelSerializer:

    class List(ListSerializer):
        """
        Get list of stock adjustment
        """
        store_point = StorePointModelSerializer.MinimalList()
        person_organization_employee = PersonOrganizationModelSerializer.MinimalList()
        class Meta(StockAdjustmentMeta):
            fields = StockAdjustmentMeta.fields + (
                'date',
                'store_point',
                'person_organization_employee',
            )
