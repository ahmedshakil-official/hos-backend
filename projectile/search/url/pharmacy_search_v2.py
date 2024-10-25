from django.urls import path

from ..view.pharmacy_search import (
    ECommerceStockProductSearchSuggestViewV2,
    ProductGroupSearchViewV2,
)


urlpatterns = [
    path(
        "stock/products/suggestions/",
        ECommerceStockProductSearchSuggestViewV2.as_view(),
        name="pharmacy.stock-search.suggestions-v2"
    ),
    path(
        "product/group/",
        ProductGroupSearchViewV2.as_view(),
        name="pharmacy-product-group-search-v2"
    ),
]
