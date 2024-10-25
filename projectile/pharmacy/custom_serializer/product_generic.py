'''
Move following serializer on this page:
<class 'pharmacy.serializers.ProductFormSerializer'>
'''
from common.custom_serializer.nsd_base_organization_wise_serializer import(
    LinkSerializer
)
from pharmacy.models import ProductGeneric


# pylint: disable=old-style-class, no-init
class ProductGenericLinkMeta(LinkSerializer.Meta):
    model = ProductGeneric
    fields = LinkSerializer.Meta.fields
    read_only_fields = LinkSerializer.Meta.read_only_fields


class ProductGenericModelSerializer:

    class Link(LinkSerializer):
        '''
        This serializer will be used to list Account model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(ProductGenericLinkMeta):
            pass
