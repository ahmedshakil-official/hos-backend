"""URLs mapping for Delivery Area/Dhaka Thana."""

from django.urls import path

from search.view.area import AreaSearchView


urlpatterns = [
    path("", AreaSearchView.as_view(), name="area-search"),
]
