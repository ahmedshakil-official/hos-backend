from rest_framework import serializers

from core.models import (
    OrganizationSetting,
)
from core.custom_serializer.organization import OrganizationModelSerializer
from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)


class OrganizationSettingMeta(ListSerializer.Meta):
    model = OrganizationSetting
    fields = ListSerializer.Meta.fields + (
        'date_format',
        'order_ending_time',
        'organization',
        'allow_order_from',
        'overwrite_order_mode_by_product',
        'order_stopping_date',
        'order_re_opening_date',
        'order_stopping_message',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # we can add readonly field here
    )


class OrganizationSettingModelSerializer:
    class List(ListSerializer):
        '''
        This serializer will be used to list OrganizationSetting model
        '''
        organization = OrganizationModelSerializer.List()

        class Meta(OrganizationSettingMeta):

            fields = OrganizationSettingMeta.fields + ()

    class Basic(ListSerializer):

        '''
        This serializer will be used to list and details OrganizationSetting model
        '''

        class Meta(OrganizationSettingMeta):
            fields = OrganizationSettingMeta.fields + ()
