from django.urls import path

from ..view.manufacturer import TopManufacturer


urlpatterns = [
    path(
        "top/",
        TopManufacturer.as_view(),
        name="top-product-manufacturer",
    ),
]
