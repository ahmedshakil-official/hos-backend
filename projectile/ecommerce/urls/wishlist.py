from django.urls import path

from ecommerce.views.wishlist import (
    WishlistItemRetrieveDelete, WishlistListCreate,
    WishlistListDetails, OrganizationWishlistItems,
    WishlistItemsStockAliasList,
)

urlpatterns = [
    path(
        'wishlist/',
        WishlistListCreate.as_view(),
        name="wishlist-list-create"
    ),
    path(
        'wishlist/<uuid:alias>/',
        WishlistListDetails.as_view(),
        name="wishlist-item-view-by-organization"
    ),
    path(
        'wishlist-items/',
        OrganizationWishlistItems.as_view(),
        name="wishlist-item-view-by-organization"
    ),
    path(
        'wishlist-item/<uuid:alias>/',
        WishlistItemRetrieveDelete.as_view(),
        name="wishlist-item-retrieve-delete"
    ),
    path(
    'wishlist-items/stocks/',
    WishlistItemsStockAliasList.as_view(),
    name="wishlist-items-stock-alias-list"
    )

]
