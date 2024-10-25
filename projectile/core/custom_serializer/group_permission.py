from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)
from ..models import GroupPermission


# pylint: disable=old-style-class, no-init
class GroupPermissionMeta(ListSerializer.Meta):
    model = GroupPermission
    fields = ListSerializer.Meta.fields + (
        'name',
        'description'
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()


class GroupPermissionModelSerializer():

    class List(ListSerializer):
        '''
        This serializer will be used to get, post in GroupPermission
        '''

        # pylint: disable=old-style-class, no-init
        class Meta(GroupPermissionMeta):
            fields = GroupPermissionMeta.fields + ()
