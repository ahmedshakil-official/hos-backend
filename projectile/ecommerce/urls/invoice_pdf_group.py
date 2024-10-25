from django.urls import path

from ecommerce.views.invoice_pdf_group import (
    InvoicePdfGroupList,
    InvoicePdfGroupDetails,
)

urlpatterns = [
    path(
        "invoice-pdf-groups/",
        InvoicePdfGroupList.as_view(),
        name="invoice-pdf-group-list"
    ),
    path(
        "invoice-pdf-groups/<uuid:alias>/",
        InvoicePdfGroupDetails.as_view(),
        name="invoice-pdf-group-details"
    ),
]
