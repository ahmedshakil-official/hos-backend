from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)

#TODO: replace this import if custom_Serializer added of these
from ..serializers import PersonOrganizationSerializer
from ..custom_serializer.group_permission import (
    GroupPermissionModelSerializer
)

from ..models import PersonOrganizationGroupPermission

# pylint: disable=old-style-class, no-init
class PersonOrganizationGroupPermissionMeta(ListSerializer.Meta):
    model = PersonOrganizationGroupPermission
    fields = ListSerializer.Meta.fields + (
        # we can add additional field here
        'person_organization',
        'permission'
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # we can add readonly field here
    )


class PersonOrganizationGroupPermissionModelSerializer:

    class Basic(ListSerializer):
        '''
        This serializer will be used to POST PersonOrganizationGroupPermission model
        '''
        # pylint: disable=old-style-class, no-init
        class Meta(PersonOrganizationGroupPermissionMeta):
            pass

    class List(ListSerializer):
        '''
        This serializer will be used to list PersonOrganizationGroupPermission model
        '''
        person_organization = PersonOrganizationSerializer()
        permission = GroupPermissionModelSerializer.List()

        # pylint: disable=old-style-class, no-init
        class Meta(PersonOrganizationGroupPermissionMeta):
            fields = PersonOrganizationGroupPermissionMeta.fields + (
                # we can add additional field here
            )
