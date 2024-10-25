from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)

from ..models import InvoiceFileStorage


# pylint: disable=old-style-class, no-init
class InvoiceFileStorageMeta(ListSerializer.Meta):
    model = InvoiceFileStorage
    fields = ListSerializer.Meta.fields + (
        'name',
        'content_type',
        'content',
        'description',
        'orders',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class InvoiceFileStorageModelSerializer:

    class List(ListSerializer):
        '''
        This serializer will be used to list InvoiceFileStorage model
        '''
        # pylint: disable=old-style-class, no-init

        class Meta(InvoiceFileStorageMeta):
            pass

