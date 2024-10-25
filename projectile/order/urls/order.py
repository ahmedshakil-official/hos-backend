"""URLs mappings for Order"""

from django.urls import path

from order.views.order import (
    DistributorReOrderV2,
    DistributorOrderPlaceV2,
    DistributorOrderLimitPerDayV2
)


urlpatterns = [
    path(
        "place/",
        DistributorOrderPlaceV2.as_view(),
        name="distributor-order-place-v2",
    ),
    path(
        "product/limit/<uuid:alias>/",
        DistributorOrderLimitPerDayV2.as_view(),
        name="distributor-product-order-limit"
    ),
    path(
        "re-order/",
        DistributorReOrderV2.as_view(),
        name="distributor-re-order-V2",
    )
]
