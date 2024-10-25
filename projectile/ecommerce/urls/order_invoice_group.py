from django.urls import path

from ..views.order_invoice_group import (
    OrderInvoiceGroupListCreate,
    OrderInvoiceGroupDetails,
    OrderInvoiceGroupStatusResponsiblePersonBulkCreate,
    ResponsibleEmployeeWiseInvoiceGroupDeliverySheetList,
    CloneOrderInvoiceGroup,
    CustomerOrderStatistics,
    InvoiceGroupListByProduct,
    InvoiceGroupStatusChangeLog,
    InvoiceGroupAdditionalDiscountMismatch,
    InvoiceGroupStatusReport,
    InvoiceGroupProductSumList,
    InvoiceGroupProductQuantityWithInvoiceCountReport,
)



urlpatterns = [

    path(
        'invoice-groups/',
        OrderInvoiceGroupListCreate.as_view(),
        name='invoice-group-list'

    ),

    path(
        'invoice-groups/<uuid:alias>/',
        OrderInvoiceGroupDetails.as_view(),
        name="invoice-group-details"

    ),
    path(
        'invoice-groups/<int:pk>/',
        OrderInvoiceGroupDetails.as_view(),
        name="invoice-group-details"

    ),
    path(
        'invoice-groups/status-responsible-person/bulk/create/',
        OrderInvoiceGroupStatusResponsiblePersonBulkCreate.as_view(),
        name="invoice-group-order-responsible-person-bulk-create"

    ),
    path(
        'invoice-groups/product-sum-list/',
        InvoiceGroupProductSumList.as_view(),
        name='invoice-group-product-list-sum-with-short-return',
    ),
    path(
        'invoice-groups/product-quantity-invoice-count/report/',
        InvoiceGroupProductQuantityWithInvoiceCountReport().as_view(),
        name='invoice-group-product-quantity-with-invoice-count-report',
    ),
    path(
        'invoice-group/delivery-sheet/',
        ResponsibleEmployeeWiseInvoiceGroupDeliverySheetList.as_view(),
        name='invoice-group-delivery-sheet-list'

    ),
    path(
        'invoice-group/clone/',
        CloneOrderInvoiceGroup.as_view(),
        name='invoice-group-clone'

    ),
    path(
        'invoice-group/statistics/',
        CustomerOrderStatistics.as_view(),
        name='invoice-group-statistics'

    ),
    path(
        'invoice-groups/fetch-by-product/',
        InvoiceGroupListByProduct.as_view(),
        name='invoice-group-fetch-by-product'

    ),
    path(
        'invoice-groups/status-change-log/<alias>/',
        InvoiceGroupStatusChangeLog.as_view(),
        name='invoice-group-fetch-all-status-change'
    ),
    path(
        'invoice-groups/discount-mismatch/',
        InvoiceGroupAdditionalDiscountMismatch.as_view(),
        name='invoice-groups-additional-discount-mismatch'
    ),
    path(
        'invoice-groups/get-status-report/',
        InvoiceGroupStatusReport.as_view(),
        name='invoice-groups-status-report'
    ),
]
