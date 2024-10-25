"""Serializer for Area Model."""

from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer
from common.validators import validate_unique_name

from core.models import Area


class AreaMeta(ListSerializer.Meta):
    model = Area
    fields = ListSerializer.Meta.fields + (
        "name",
        "slug",
        "code",
        "discount_factor",
        "description",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        "slug",
    )


class AreaModelSerializer:
    class List(ListSerializer):
        class Meta(AreaMeta):
            fields = AreaMeta.fields + (
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
            )

        def validate_name(self, value):
            if validate_unique_name(self, value, Area, "name"):
                return value
            else:
                raise serializers.ValidationError({"detail": f"Area with name: {value}, already exists."})

    class Detail(ListSerializer):
        class Meta(AreaMeta):
            fields = AreaMeta.fields + (
                "status",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
            )

        def validate_name(self, value):
            # If a similar name exists, raise a validation error with a detail message
            if validate_unique_name(self, value, Area, "name"):
                return value
            else:
                raise serializers.ValidationError({"detail": f"Area with name: {value}, already exists."})


    class NameOnly(ListSerializer):
        class Meta(AreaMeta):
            fields = (
                "name",
            )

    class BulkUpdateSerializer(serializers.ModelSerializer):
        """Serializer for updating discount factor"""

        alias = serializers.UUIDField()

        class Meta:
            model = Area
            fields = (
                "alias",
                "discount_factor"
            )
