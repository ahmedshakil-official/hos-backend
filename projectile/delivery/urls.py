from django.urls import path

from . import views

# pylint: disable=invalid-name
urlpatterns = [
    path('', views.DeliveryList.as_view(), name='delivery-list'),
    path('<uuid:alias>/', views.DeliveryDetails.as_view(), name='delivery-details'),
    path('<uuid:delivery_alias>/products/<uuid:product_alias>/', views.UpdateStockDelivery.as_view(), name='update-stock-delivery'),
]
