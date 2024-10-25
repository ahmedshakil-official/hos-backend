from django.urls import path

from ecommerce.views.order_delivery_rating import OrderRatingListCreate

urlpatterns = [
    path(
        'order-rating/',
        OrderRatingListCreate.as_view(),
        name='invoice-groups-order-rating'
    )

]
