from rest_framework.serializers import (
    ModelSerializer,
)

class ListSerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        ref_name = ''
        fields = (
            'id',
            'alias',

        )
        read_only_fields = (
            'id',
            'alias'
        )


class LinkSerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        ref_name = ''
        fields = (
            'id',
            'alias',

        )
        read_only_fields = (
            'id',
        )
