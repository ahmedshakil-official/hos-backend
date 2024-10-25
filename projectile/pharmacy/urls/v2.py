from django.urls import re_path, path

from ..view.purchase import (
    DistributorOrderCartCreateOrUpdate,
    DistributorOrderRatings
)
from ..view.stock import (
    DistributorSalesAbleStockProductListV2,
    DistributorSalesAbleStockRecentOrderedProductListV2,
    DistributorSalesAbleStockBestDiscountProductListV2,
    DistributorSalesAbleStockLatestProductListV2,
    GetProductSortingOptionsV2,
)

urlpatterns = [

    # Distributor order related urls
    re_path(
        r'^distributor/order/cart/$',
        DistributorOrderCartCreateOrUpdate.as_view(),
        name="distributor-order-cart-list-create-v2"
    ),
    path(
        'distributor/stocks/products/',
        DistributorSalesAbleStockProductListV2.as_view(),
        name='distributor-stock-product-list-v2'
    ),
    path(
        'distributor/stocks/products/get-sorting-options/',
        GetProductSortingOptionsV2.as_view(),
        name="get-product-sorting-options-v2"
    ),
    path(
        'distributor/stocks/products/recent/',
        DistributorSalesAbleStockRecentOrderedProductListV2.as_view(),
        name='distributor-stock-product-list-recent-v2'
    ),
    path(
        'distributor/stocks/products/best-discount/',
        DistributorSalesAbleStockBestDiscountProductListV2.as_view(),
        name='distributor-stock-product-list-best-discount-v2'
    ),
    path(
        'distributor/stocks/products/latest/',
        DistributorSalesAbleStockLatestProductListV2.as_view(),
        name='distributor-stock-latest-product-list'
    ),
    path(
        "distributor/orders-ratings/",
        DistributorOrderRatings.as_view(),
        name="distributors-order-ratings"
    )
]

