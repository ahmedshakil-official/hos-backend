from django.urls import re_path

from . import views

# pylint: disable=invalid-name
urlpatterns = [
    re_path(r'^$', views.PromotionList.as_view(), name="promotion-list"),
    re_path(r'^published/$', views.PublishPromotion.as_view(), name="published-promotion-list"),
    # re_path(r'^published/(?P<alias>[\w-]+)/$', views.PublishPromotionDetails.as_view(),
    #     name="published-promotion-details"),
    re_path(r'^(?P<alias>[\w-]+)/$', views.PromotionDetails.as_view(), name="promotion-details"),
    re_path(r'^published/bulk/$', views.PromotionBulkPublish.as_view(),
        name="bulk-published-promotion"),
    re_path(r'^published/orders/$', views.PublishedPromotionOrderList.as_view(),
        name="published-promotion-orders"),
    re_path(r'^published/orders/(?P<alias>[\w-]+)/$', views.PublishedPromotionOrderDetails.as_view(),
        name="published-promotion-order-details"),
    re_path(r'^popup/messages/published/$', views.PublishPopUpMessage.as_view(),
        name="published-popup-message-list"),
    re_path(r'^popup/messages/published/bulk/$', views.PopUpMessageBulkPublish.as_view(),
        name="published-popup-message-bulk"),
    re_path(r'^popup/messages/published/log/(?P<alias>[\w-]+)/$', views.PublishedPopUpMessageLogList.as_view(),
        name="published-popup-message-log-list"),
    re_path(r'^popup/messages/$', views.PopUpMessageList.as_view(), name="popup-message-list"),
    re_path(r'^popup/messages/(?P<alias>[\w-]+)/$', views.PopUpMessageDetails.as_view(),
        name="popup-message-details"),
]
