from django.utils import timezone

from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer
)
from common .enums import Status
from core.custom_serializer.organization import (
    OrganizationModelSerializer,
)
from .popup_message import PopUpMessageModelSerializer
from ..models import PublishedPopUpMessage

class PublishedPopUpMessageMeta(ListSerializer.Meta):
    model = PublishedPopUpMessage

    fields = ListSerializer.Meta.fields + (
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class PublishedPopUpMessageModelSerializer:

    class Lite(ListSerializer):

        class Meta(PublishedPopUpMessageMeta):
            fields = PublishedPopUpMessageMeta.fields + (
                'message',
            )

    class Basic(ListSerializer):

        class Meta(PublishedPopUpMessageMeta):
            fields = PublishedPopUpMessageMeta.fields + (
                'organization',
                'message',
            )

        def create(self, validated_data):
            popup_message, created = PublishedPopUpMessage.objects.get_or_create(
                publish_date=timezone.now(),
                status=Status.ACTIVE,
                **validated_data
            )
            if created:
                popup_message.save()
            return popup_message

    class List(ListSerializer):
        message = PopUpMessageModelSerializer.List()
        organization = OrganizationModelSerializer.Lite()

        class Meta(PublishedPopUpMessageMeta):
            fields = PublishedPopUpMessageMeta.fields + (
                'status',
                'message',
                'organization',
            )


class PublishedPopUpMessageLogSerializer(serializers.Serializer):
    date = serializers.DateField()
    publish_count = serializers.IntegerField()
    unpublish_count = serializers.IntegerField()
