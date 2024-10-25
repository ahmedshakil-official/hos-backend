from django.urls import path, register_converter
from ..views.delivery_sheet_invoice_group import (
    DeliverySheetInvoiceGroupReport
)


urlpatterns = [
    path(
        'delivery-sheet-invoice-group/report/',
        DeliverySheetInvoiceGroupReport.as_view(),
        name='delivery-sheet-invoice-group-report'
    ),
]
