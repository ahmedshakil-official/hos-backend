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
            'name',
            'description',
            'is_global',
            'status',
        )
        read_only_fields = (
            'id',
            'alias'
        )


class MiniListSerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        ref_name = ''
        fields = (
            'id',
            'alias',
            'name',
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
            'name',
        )
        read_only_fields = (
            'id',
            'alias'
            'name',
        )


class CodeBaseSerializer(ModelSerializer):

    # pylint: disable=old-style-class, no-init
    class Meta:
        ref_name = ''
        fields = (
            'id',
            'alias',
            'name',
            'code',
        )
        read_only_fields = (
            'id',
            'alias',
        )
