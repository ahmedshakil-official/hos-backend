from rest_framework.serializers import ValidationError

from common.custom_serializer.nsd_base_organization_wise_serializer import(
    ListSerializer, LinkSerializer
)
from common.custom_serializer_field import CustomVersatileImageFieldSerializer

from common.validators import (
    validate_unique_name_with_org
)

from ..models import ProductCategory


# pylint: disable=old-style-class, no-init
class ProductCategoryMeta(ListSerializer.Meta):
    model = ProductCategory
    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProductCategoryModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to list ProductCategory model
        '''
        logo = CustomVersatileImageFieldSerializer(
            sizes='logo_images',
            required=False
        )
        def validate_name(self, value):
            if not validate_unique_name_with_org(self, value, ProductCategory):
                raise ValidationError('YOU_HAVE_ALREADY_A_CATEGORY_WITH_SAME_NAME')

            return value

        # pylint: disable=old-style-class, no-init

        class Meta(ProductCategoryMeta):
            fields = ProductCategoryMeta.fields + (
                "logo",
            )
            read_only_fields = ProductCategoryMeta.read_only_fields + ()

    class Details(List):
        '''
        This serializer will be used to see details of ProductCategory model
        '''
        # pylint: disable=old-style-class, no-init
        logo = CustomVersatileImageFieldSerializer(
            sizes='logo_images',
            required=False
        )
        class Meta(ProductCategoryMeta):
            fields = ProductCategoryMeta.fields + (
                "logo",
            )
            read_only_fields = ProductCategoryMeta.read_only_fields + ()

    class Link(LinkSerializer):
        '''
        This serializer will be used to see minimal items of ProductCategory model
        '''
        # pylint: disable=old-style-class, no-init
        class Meta(ProductCategoryMeta):
            fields = LinkSerializer.Meta.fields + (
                # we can add additional field here
            )
