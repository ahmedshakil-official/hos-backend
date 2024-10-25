'''
Move following serializer on this page:
<class 'pharmacy.serializers.ProductFormSerializer'>
'''

from common.custom_serializer.nsd_base_organization_wise_serializer import(
    LinkSerializer
)
from pharmacy.models import ProductGroup


# pylint: disable=old-style-class, no-init
class ProductGroupLinkMeta(LinkSerializer.Meta):
    model = ProductGroup
    fields = LinkSerializer.Meta.fields + ('type', )
    read_only_fields = LinkSerializer.Meta.read_only_fields


class ProductGroupModelSerializer:

    class Link(LinkSerializer):
        '''
        This serializer will be used to list Account model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(ProductGroupLinkMeta):
            pass
