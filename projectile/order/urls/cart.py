"""URLs mappings for Cart"""

from django.urls import path

from order.views.cart import DistributorOrderCartListCreateV2


urlpatterns = [
    path(
        "cart/",
        DistributorOrderCartListCreateV2.as_view(),
        name="distributor-order-cart-list-create-v2",
    ),
]
