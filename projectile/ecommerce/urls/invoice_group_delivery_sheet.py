from django.urls import path, register_converter
from ..views.invoice_group_delivery_sheet import (
    InvoiceGroupDeliverySheetListCreate,
    InvoiceGroupDeliverySheetDetails,
    DeliverySheetShortReturnListProductWise,
    DeliverySheetStockShortReturnListInvoiceGroupWise,
    DeliverySheetDataSpecificDayWise,
    InvoiceGroupDeliverySheetInfo,
    FixInvoiceGroupDeliverySheetMismatch,
    DeliverySheetOrganizationPrimaryResponsiblePerson,
    AssignedUnAssignedDelivery,
    CompletedDeliveriesCount,
)

from ..views.invoice_group_delivery_sub_sheet import InvoiceGroupDeliverySubSheetCreate

from common.converters import DateConverter

register_converter(DateConverter, 'date')


urlpatterns = [

    path(
        'invoice-group/delivery-sheets/',
        InvoiceGroupDeliverySheetListCreate.as_view(),
        name='invoice-group-delivery-sheet-list'

    ),

    path(
        'invoice-group/delivery-sheets/<uuid:alias>/',
        InvoiceGroupDeliverySheetDetails.as_view(),
        name='invoice-group-delivery-sheet-details'

    ),
    path(
        'invoice-group/delivery-sheets/<int:pk>/',
        InvoiceGroupDeliverySheetDetails.as_view(),
        name='invoice-group-delivery-sheet-details'

    ),
    path(
        'delivery-sheet/<int:delivery_sheet_id>/short-return/item-wise/',
        DeliverySheetShortReturnListProductWise.as_view(),
        name='delivery-sheet-short-return-item-wise'

    ),
    path(
        'delivery-sheet/<int:delivery_sheet_id>/stock/<uuid:stock_alias>/short-return/invoice-wise/',
        DeliverySheetStockShortReturnListInvoiceGroupWise.as_view(),
        name='delivery-sheet-stock-short-return-invoice-wise'

    ),
    path(
        "invoice-group-delivery-sheet/<int:id>/organizations-primary-responsible-person/",
        DeliverySheetOrganizationPrimaryResponsiblePerson.as_view(),
        name="invoice-group-delivery-sheet",
    ),
    path(
        "invoice-group-delivery-sheet/completed-deliveries/",
        CompletedDeliveriesCount.as_view(),
        name="top-sheet-completed-deliveries-count",
    ),
    path(
        "invoice-group-delivery-sheet/<uuid:alias>/organizations-primary-responsible-person/",
        DeliverySheetOrganizationPrimaryResponsiblePerson.as_view(),
        name="invoice-group-delivery-sheet",
    ),
    path(
        'invoice-group/delivery-sheet/<uuid:responsible_employee_alias>/<date:date>/',
        DeliverySheetDataSpecificDayWise.as_view(),
        name='invoice-group-delivery-sheet'
    ),
    path(
        'invoice-group/delivery-sheets/<int:pk>/info/',
        InvoiceGroupDeliverySheetInfo.as_view(),
        name='invoice-group-delivery-sheet-info'

    ),
    path(
        'invoice-group/delivery-sheets/fix-mismatch/<uuid:alias>/',
        FixInvoiceGroupDeliverySheetMismatch.as_view(),
        name='invoice-group-delivery-sheet-fix-mismatch'
    ),
    path(
        "invoice-group/delivery-sheet/<uuid:alias>/deliveries/",
        AssignedUnAssignedDelivery.as_view(),
        name="assigned-unassigned-delivery-top-sheet"
    ),
    path(
        "invoice-group/delivery-sheet/sub-top-sheets/create/",
        InvoiceGroupDeliverySubSheetCreate.as_view(),
        name="invoice-group-delivery-sub-sheet-create",
    ),
]
