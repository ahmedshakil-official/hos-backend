from common.custom_serializer.nsd_base_organization_wise_serializer import(
    LinkSerializer
)
from pharmacy.models import ProductCompartment


# pylint: disable=old-style-class, no-init
class ProductCompartmentMeta(LinkSerializer.Meta):
    model = ProductCompartment
    fields = LinkSerializer.Meta.fields + (
        'name',
        'priority',
    )
    read_only_fields = LinkSerializer.Meta.read_only_fields


class ProductCompartmentModelSerializer:

    class Link(LinkSerializer):
        '''
        This serializer will be used to list Account model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(ProductCompartmentMeta):
            pass


    class MinimalList(LinkSerializer):
        """
        Get list of units
        """
        class Meta(ProductCompartmentMeta):
            pass
