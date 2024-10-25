from django.contrib import admin
from common.admin import CreatedAtUpdatedAtBaseModel
from .models import PushToken, PushNotification, Notification, OrganizationNotificationConnector


class PushTokenAdmin(CreatedAtUpdatedAtBaseModel):
    pass


class PushNotificationAdmin(CreatedAtUpdatedAtBaseModel):
    pass


class NotificationAdmin(CreatedAtUpdatedAtBaseModel):
    pass


class OrganizationConnectorForNotificationAdmin(CreatedAtUpdatedAtBaseModel):
    pass


admin.site.register(PushToken, PushTokenAdmin)
admin.site.register(PushNotification, PushNotificationAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(OrganizationNotificationConnector, OrganizationConnectorForNotificationAdmin)
