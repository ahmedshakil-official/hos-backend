from django.urls import path

from core.views.delivery_hub import (
    DeliveryHubList, DeliveryHubDetail
)
urlpatterns = [
    path("", DeliveryHubList.as_view(), name="delivery-hub-list-create"),
    path("<uuid:alias>/", DeliveryHubDetail.as_view(), name="delivery-hub-details"),
]
