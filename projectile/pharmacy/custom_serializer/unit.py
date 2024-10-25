'''
Move following serializer on this page:
<class 'pharmacy.serializers.ProductFormSerializer'>
'''
from common.custom_serializer.nsd_base_organization_wise_serializer import(
    LinkSerializer
)
from pharmacy.models import Unit


# pylint: disable=old-style-class, no-init
class UnitLinkMeta(LinkSerializer.Meta):
    model = Unit
    fields = LinkSerializer.Meta.fields + (
        'name',
    )
    read_only_fields = LinkSerializer.Meta.read_only_fields


class UnitModelSerializer:

    class Link(LinkSerializer):
        '''
        This serializer will be used to list Account model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(UnitLinkMeta):
            pass


    class MinimalList(LinkSerializer):
        """
        Get list of units
        """
        class Meta(UnitLinkMeta):
            pass
