from django.urls import path, register_converter
from ..views.common import (
    FetchingDeliveryDate,
    DownloadInvoiceFiles,
)


urlpatterns = [
    path(
        'get-delivery-date/',
        FetchingDeliveryDate.as_view(),
        name='order-delivery-date'
    ),
    path(
        'download-invoice-files/',
        DownloadInvoiceFiles.as_view(),
        name='download-invoice-filesp'
    ),
]
