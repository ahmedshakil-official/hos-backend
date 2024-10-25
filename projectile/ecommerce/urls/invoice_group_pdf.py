from django.urls import path

from ecommerce.views.invoice_group_pdf import (
    InvoiceGroupPDFList,
    InvoiceGroupPdfDetails,
)

urlpatterns = [
    path(
        "invoice-group-pdfs/",
        InvoiceGroupPDFList.as_view(),
        name="invoice-pdf-list"
    ),
    path(
        "invoice-group-pdfs/<uuid:alias>/",
        InvoiceGroupPdfDetails.as_view(),
        name="invoice-pdf-view-by-invoice-group"
    ),
]
