from rest_framework.serializers import (
    ModelSerializer,
)


class NameOnlySerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        ref_name = ''
        fields = (
            'id',
            'name',
        )
        read_only_fields = (
            'id',
            'name',
        )
