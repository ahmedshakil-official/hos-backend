from django.urls import re_path
from ..view.ecommerce import (
    OrderInvoiceGroupSearchView,
)

urlpatterns = [
    re_path(r'^invoice-groups/$', OrderInvoiceGroupSearchView.as_view(), name='order-invoice-group-search'),
]
