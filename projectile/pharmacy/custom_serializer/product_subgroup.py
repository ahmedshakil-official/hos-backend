'''
Move following serializer on this page:
<class 'pharmacy.serializers.ProductFormSerializer'>
'''
from common.custom_serializer.nsd_base_organization_wise_serializer import(
    LinkSerializer, MiniListSerializer
)
from pharmacy.models import ProductSubgroup


# pylint: disable=old-style-class, no-init
class ProductSubgroupMiniListMeta(MiniListSerializer.Meta):
    model = ProductSubgroup
    fields = LinkSerializer.Meta.fields + ('product_group',)
    read_only_fields = LinkSerializer.Meta.read_only_fields


class ProductSubgroupModelSerializer:

    class List(MiniListSerializer):
        '''
        This serializer will be used to list Account model
        '''
        # pylint: disable=old-style-class, no-init
        from pharmacy.custom_serializer.product_group import ProductGroupModelSerializer
        product_group = ProductGroupModelSerializer.Link()

        class Meta(ProductSubgroupMiniListMeta):
            pass
