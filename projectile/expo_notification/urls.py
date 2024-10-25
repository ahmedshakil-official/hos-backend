from django.urls import re_path, path

from . import views

# pylint: disable=invalid-name
urlpatterns = [
    re_path(r'^register-push-token/$', views.RegisterPushToken.as_view(),
        name="resister-push-token"),
    re_path(r'^push-notifications/$', views.PushNotificationList.as_view(),
        name="push-notification-list-create"),
    re_path(r'^user/notifications/$', views.UserNotificationList.as_view(),
        name="user-notification-list"),
    re_path(r'^user/notifications/(?P<alias>[\w-]+)/$', views.UserNotificationDetails.as_view(),
        name="user-notification-details"),
    re_path(r'^count/$', views.NotificationCount.as_view(),
        name="user-notification-count"),
    re_path(r'^mark-all-as-read/$', views.MarkAllNotificationAsRead.as_view(),
        name="mark-all-notification-as-read"),
    path(
        'notifications-list-create/',
        views.NotificationListCreate.as_view(),
        name='list-create-notification'
    )
]
