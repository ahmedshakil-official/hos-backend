from django.db import models
from django.utils.translation import gettext as _

# Create your models here.
import datetime

from django.db import models
from django.db.models.fields import DateField
from django.db.models.functions import Cast
from django.db.models.signals import post_save

from django.db.models import (
    CharField,
)
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import ArrayAgg
from django.conf import settings

from enumerify import fields

from common.fields import TimestampVersatileImageField
from common.models import CreatedAtUpdatedAtBaseModel
from core.models import Organization
from .enums import DeviceType
from .signals import post_save_expo_notification


class PushToken(CreatedAtUpdatedAtBaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        blank=True,
        null=True
    )
    token = models.CharField(max_length=255, null=True, blank=True)
    player_id = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    active = models.BooleanField(default=False)
    device_type = fields.SelectIntegerField(blueprint=DeviceType, default=DeviceType.ANDROID)
    app_version = models.CharField(
        max_length=24,
        blank=True,
        null=True,
        default=None
    )


    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.device_type, self.user)


class Notification(CreatedAtUpdatedAtBaseModel):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        blank=True,
        null=True
    )
    body = models.TextField()
    data = models.TextField()
    image = TimestampVersatileImageField(upload_to='notification/', null=True, blank=True)
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    def get_queryset_for_cache(self, list_of_pks=None, request=None):
        if list_of_pks is None or len(list_of_pks) == 0:
            list_of_pks = [self.id]

        queryset = self.__class__.objects.filter(
            pk__in=list_of_pks
        ).annotate(
            organizations=ArrayAgg(Cast('organizations_notification__organization__name', CharField())),
        ).order_by('-id')

        return queryset

    def __str__(self):
        return str(self.title) + " - " + str(self.body)


class OrganizationNotificationConnector(CreatedAtUpdatedAtBaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.DO_NOTHING,
        related_name='organizations_notification'
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.DO_NOTHING,
        related_name='organizations_notification'
    )

    def __str__(self):
        return str(self.organization) + " - " + str(self.notification)


class PushNotification(CreatedAtUpdatedAtBaseModel):
    """Push Notification"""
    token = models.ForeignKey(PushToken, on_delete=models.DO_NOTHING)
    title = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        blank=True,
        null=True
    )
    body = models.TextField()
    data = models.TextField()
    response = models.TextField(null=True, blank=True)
    notification = models.ForeignKey(Notification, on_delete=models.DO_NOTHING, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.DO_NOTHING)
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.body

    def get_queryset_for_cache(self, list_of_pks=None, request=None):
        '''
        This method take a list of primary key of PushNotification and return queryset to cache them
        Parameters
        ----------
        self : core.expo_notification.PushNotification
            An instance of core.expo_notification.PushNotification model
        list_of_pks : list
            list of primary key of Sales it can be None of empty list
        Raises
        ------
        No error is raised by this method
        Returns
        -------
        queryset
            This method return queryset for given PushNotification instance's pk
        '''
        if list_of_pks is None or len(list_of_pks) == 0:
            list_of_pks = [self.id]

        queryset = self.__class__.objects.filter(
            pk__in=list_of_pks
        ).annotate(
            organizations=ArrayAgg(Cast('user__organization__name', CharField()), distinct=True),
            date=Cast('created_at', DateField())
        )

        return queryset


post_save.connect(post_save_expo_notification, sender=PushNotification)
