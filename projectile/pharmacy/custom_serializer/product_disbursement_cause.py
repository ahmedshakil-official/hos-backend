from rest_framework.serializers import ValidationError
from common.custom_serializer.nsd_base_organization_wise_serializer import(
    ListSerializer, LinkSerializer
)

from common.validators import (
    validate_unique_name_with_org
)

from ..models import ProductDisbursementCause


# pylint: disable=old-style-class, no-init
class ProductDisbursementCauseMeta(ListSerializer.Meta):
    model = ProductDisbursementCause
    fields = ListSerializer.Meta.fields + (
        # we can add additional field here
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProductDisbursementCauseModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to list ProductDisbursementCause model
        '''
        def validate_name(self, value):
            if not validate_unique_name_with_org(self, value, ProductDisbursementCause):
                raise ValidationError(
                    'YOU_ALREADY_HAVE_A_PRODUCT_DISBURSEMENT_CAUSE_WITH_SAME_NAME')
            return value

        # pylint: disable=old-style-class, no-init
        class Meta(ProductDisbursementCauseMeta):
            pass

    class Link(LinkSerializer):
        class Meta(ProductDisbursementCauseMeta):
            fields = LinkSerializer.Meta.fields + (
                # we can add additional field here
            )
