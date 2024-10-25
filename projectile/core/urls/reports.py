from django.urls import re_path
from ..views.organizations import (
    DistributorBuyerOrderSummary, DistributorBuyerOrderHistory
)

urlpatterns = [
    re_path(
        r'distributor-buyer-order-summary/$',
        DistributorBuyerOrderSummary.as_view(),
        name="distributor-buyer-order-summary"
    ),
    re_path(
        r'distributor-buyer-order-history/$',
        DistributorBuyerOrderHistory.as_view(),
        name="distributor-buyer-order-history"
    )
]
