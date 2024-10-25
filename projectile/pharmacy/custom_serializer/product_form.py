'''
Move following serializer on this page:
<class 'pharmacy.serializers.ProductFormSerializer'>
'''
from common.custom_serializer.nsd_base_organization_wise_serializer import(
    LinkSerializer
)
from common.custom_serializer.name_only_serializer import NameOnlySerializer
from pharmacy.models import ProductForm


# pylint: disable=old-style-class, no-init
class ProductFormLinkMeta(LinkSerializer.Meta):
    model = ProductForm
    fields = LinkSerializer.Meta.fields
    read_only_fields = LinkSerializer.Meta.read_only_fields


class ProductFormModelSerializer:

    class Link(LinkSerializer):
        '''
        This serializer will be used to list Account model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(ProductFormLinkMeta):
            pass


    class NameOnly(NameOnlySerializer):
        '''
        This serializer will be used to serialize name only
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(ProductFormLinkMeta):
            pass
