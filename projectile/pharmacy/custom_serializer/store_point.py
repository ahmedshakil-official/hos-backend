'''
Move following serializer on this page:
<class 'pharmacy.serializers.StorePointSerializer'>
'''

from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from ..models import StorePoint


class StorePointMeta(ListSerializer):
    model = StorePoint
    fields = ListSerializer.Meta.fields + (
        'name',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # we can add readonly field here
    )


class StorePointModelSerializer:

    class MinimalList(ListSerializer):
        """
        Get list of store point
        """
        class Meta(StorePointMeta):
            pass

    class LiteList(ListSerializer):
        """
        Get lite list of store point
        """
        class Meta(StorePointMeta):
            fields = StorePointMeta.fields + (
                'phone',
                'address',
                'type',
            )
