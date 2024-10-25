import ast

from attr.converters import to_bool
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from versatileimagefield.serializers import VersatileImageFieldSerializer

from common.enums import Status
from core.models import Organization
from .models import PushToken, PushNotification, Notification, OrganizationNotificationConnector


class PushTokenSerializer(ModelSerializer):
    class Meta:
        model = PushToken
        fields = (
            'id',
            'alias',
            'name',
            'token',
            'player_id',
            'user',
            'active',
            'device_type',
        )
        read_only_fields = (
            'id',
            'alias',
        )

    def create(self, validated_data):
        request = self.context.get('request')
        _object = None
        app_version = request.headers.get('X-App-Version', None)
        validated_data['entry_by_id'] = validated_data.get('user').id
        validated_data['user_id'] = validated_data.pop('user').id
        try:
            _object = PushToken.objects.get(**validated_data)
            if app_version and _object.app_version != app_version:
                _object.app_version = app_version
                _object.updated_by = request.user
                _object.save(update_fields=['app_version', 'updated_by'])
        except PushToken.DoesNotExist:
            _object = PushToken.objects.create(**validated_data)
            if app_version:
                _object.app_version = app_version
            _object.save()
        except PushToken.MultipleObjectsReturned:
            _object = PushToken.objects.filter(**validated_data).last()
            if app_version and _object.app_version != app_version:
                _object.app_version = app_version
                _object.updated_by = request.user
                _object.save(update_fields=['app_version', 'updated_by'])
        # Inactive all tokens except current
        PushToken.objects.filter(
            user_id=validated_data.get('user_id')
        ).exclude(pk=_object.pk).update(active=False)
        return _object


class PushNotificationListSerializer(ModelSerializer):
    organizations = serializers.ListField(read_only=True)
    date = serializers.DateField(read_only=True)

    class Meta:
        model = PushNotification
        fields = (
            'title',
            'body',
            'date',
            'organizations',
        )
        read_only_fields = (
            'date',
            'organizations',
        )


class UserNotificationListSerializer(ModelSerializer):
    class Meta:
        model = PushNotification
        fields = (
            'alias',
            'title',
            'url',
            'body',
            'created_at',
            'status',
        )


class NotificationSerializer:
    class List(ModelSerializer):
        organizations = serializers.ListField(required=False)
        data = serializers.JSONField(required=False)

        class Meta:
            model = Notification
            fields = (
                'id',
                'alias',
                'title',
                'body',
                'data',
                'image',
                'url',
                'organizations',
                'created_at',
                'updated_at',
                'status',
            )
            read_only_fields = (
                'id',
                'created_at',
                'updated_at',
                'status'
            )

        def create(self, validated_data):
            send_notification_to_all_users = self.context.get('request').data.get('send_notification_to_all_user', False)
            send_notification_to_all_users = to_bool(send_notification_to_all_users) if send_notification_to_all_users else False
            organization = validated_data.pop('organizations', None)
            notification = Notification.objects.create(**validated_data)
            if notification.image:
                notification_img_warmer = VersatileImageFieldWarmer(
                    instance_or_queryset=notification,
                    rendition_key_set='notification_images',
                    image_attr='image',
                )
                num_created, failed_to_create = notification_img_warmer.warm()
            obj_to_create = []
            if organization and send_notification_to_all_users is False:
                organization = ast.literal_eval(organization[0])
                for org in organization:
                    obj_to_create.append(
                        OrganizationNotificationConnector(
                            organization_id=org,
                            notification=notification
                        )
                    )
                OrganizationNotificationConnector.objects.bulk_create(obj_to_create)
            if send_notification_to_all_users is True:
                organizations = Organization.objects.filter(
                    status=Status.ACTIVE
                ).only('id')
                for org in organizations:
                    obj_to_create.append(
                        OrganizationNotificationConnector(
                            organization_id=org.id,
                            notification=notification
                        )
                    )
                OrganizationNotificationConnector.objects.bulk_create(obj_to_create)

            return notification

    class ImageOnly(ModelSerializer):
        image = VersatileImageFieldSerializer(
            sizes='notification_images',
            required=False,
        )

        class Meta:
            model = Notification
            fields = (
                'alias',
                'image',
            )


class UserNotificationDetailsSerializer(ModelSerializer):
    notification = NotificationSerializer.ImageOnly()

    class Meta:
        model = PushNotification
        fields = (
            'alias',
            'title',
            'body',
            'url',
            'notification',
            'created_at',
            'status',
        )

