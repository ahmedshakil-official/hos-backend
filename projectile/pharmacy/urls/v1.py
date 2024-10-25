from django.urls import path, re_path

from .. import views
from ..view.product_changes_logs import ProductChangesLogsList, ProductChangesLogsDetail
from ..view.product_reminder import (
    ProductRestockReminderListCreate, ProductRestockReminderUpdate,
    OrganizationWiseProductRestockReminderList
)
from ..view.stock import (
    SalesAbleStockProductCachedList,
    StockProductCachedList,
    DistributorSalesAbleStockProductList,
    DistributorSalesAbleStockFlashProductList,
    DistributorSalesAbleStockTrendingProductList,
    DistributorSalesAbleStockRecentOrderedProductList,
    DistributorStockDetails,
    DistributorSalesAbleStockRecommendedProductList,
    DistributorSalesAbleStockSimilarProductList,
    StockChangeHistory, GetProductSortingOptions,
)
from ..view.purchase import (
    DistributorOrderCartListCreate,
    DistributorOrderDetails,
    DistributorOrderListCreate,
    DistributorNonGroupedOrderList,
    DistributorOrderStatusChangeLogList,
    DistributorOrderStats,
    OrderStatusResponsiblePersonBulkCreate,
    OrderBulkStatusUpdate,
    OrderClone,
    DistributorReOrder,
    ProcessingToDeliverStockList,
    RequisitionRelatedPurchaseOrderProcurement,
    CancelOrderFromCustomerEnd, OrderPreOrderGraphList,
)
from ..view.invoice_pdf import GeneratePdfInvoice, OrderPdfInvoiceList
from ..view.order_tracking import OrderTrackingList, OrderTrackingStatusChangeLog
from ..view.reports import (
    SalesPurchaseStockValueGroupWiseSummary,
    DistributorOrderProductSummary,
    ProductWiseDistributorOrderDiscountSummary,
    DateAndStatusWiseOrderAmount,
    ResponsibleEmployeeWiseDeliverySheetList,
    ProductWiseStockTransferReport,
    MismatchedStockWithIOProductList,
)
from ..view.su_reports import (
    DistributorOrganizationOrderSummary,
)

from ..view.supplier_product_log import (
    PurchaseSupplierProductReceivedHistory,
)

from ..view.log import (
    OrderDetails, )
from ..view.purchase_discount import GetDiscountRules

from ..view.predictions import (
    PurchasePrediction,
    AdvPurchasePrediction,
    StockWritingFormat,
    LossProduct,
    DistributorOrderPurchasePrediction,
)

from ..view.organization_invoice_history import OrganizationOrderInvoiceHistory
from ..view.purchase_supplier_product_history import (
    PurchaseSupplierInvoiceProductHistory,
    SupplierPurchaseHistory,
)

from ..view.product_compartment import ProductCompartmentList

from ..view.invoice_status_change_log import InvoiceStatusChangeLog

from ..view.product import (
    ProductPropertiesBulkUpdate,
    ProductListFetchByStockId,
    DamageProductList,
    DamageProductDetail,
    RecheckProductList,
    RecheckProductDetail,
    DamageItemsList,
    RecheckItemsList,
    RecheckItemsDetail
)



urlpatterns = [
    path('product/changes-logs/',
        ProductChangesLogsList.as_view(),
        name='product-changes-log-list'
        ),
    path('product/changes-logs/<uuid:product__alias>/',
        ProductChangesLogsDetail.as_view(),
        name='product-changes-log-details-by-product'
        ),
    re_path(r'^product/compartments/$', ProductCompartmentList.as_view(),
        name="pharmacy.product.compartment-list"),
    re_path(r'^product/form/$', views.ProductFormList.as_view(),
        name="pharmacy.product.form-list"),
    # re_path(r'^product/form/search/$', views.ProductFormSearch.as_view(),
    #     name="pharmacy.product.form-search"),
    re_path(r'product/form/(?P<alias>[\w-]+)/$', views.ProductFormDetails.as_view(),
        name="pharmacy.product.form-details"),

    re_path(r'^product/manufacturer/$', views.ProductManufacturingCompanyList.as_view(),
        name="pharmacy.product.manufacturer-list"),
    # re_path(r'^product/manufacturer/search/$', views.ProductManufacturingCompanySearch.as_view(),
    #     name="pharmacy.product.manufacturer-search"),
    re_path(r'^product/manufacturer/(?P<alias>[\w-]+)/$',
        views.ProductManufacturingCompanyDetails.as_view(),
        name="pharmacy.product.manufacturer-details"),

    re_path(r'^product/group/$', views.ProductGroupList.as_view(),
        name="pharmacy.product.group-list"),
    # re_path(r'^product/group/search/$', views.ProductGroupSearch.as_view(),
    #     name="pharmacy.product.group-search"),
    re_path(r'^product/group/(?P<alias>[\w-]+)/$', views.ProductGroupDetails.as_view(),
        name="pharmacy.product.group-details"),

    re_path(r'^product/subgroup/$', views.ProductSubgroupList.as_view(),
        name="pharmacy.product.subgroup-list"),
    # re_path(r'^product/subgroup/search/$', views.ProductSubgroupSearch.as_view(),
    #     name="pharmacy.product.subgroup-search"),
    re_path(r'^product/subgroup/(?P<alias>[\w-]+)/$', views.ProductSubgroupDetails.as_view(),
        name="pharmacy.product.subgroup-details"),

    re_path(r'^product/generic/$', views.ProductGenericList.as_view(),
        name="pharmacy.product.generic-list"),
    # re_path(r'^product/generic/search/$', views.ProductGenericSearch.as_view(),
    #     name="pharmacy.product.generic-search"),
    re_path(r'^product/generic/(?P<alias>[\w-]+)/$', views.ProductGenericDetails.as_view(),
        name="pharmacy.product.generic-details"),

    re_path(r'^product/category/$', views.ProductCategoryList.as_view(),
        name="pharmacy.product.category-list"),
    re_path(r'^product/category/(?P<alias>[\w-]+)/$', views.ProductCategoryDetails.as_view(),
        name="pharmacy.product.category-details"),
    re_path(r'^product/sales/vat/$', views.SalesVatReport.as_view(),
        name="pharmacy.product.sales-vat-report"),
    re_path(r'^product/purchase/$', views.PurchaseList.as_view(),
        name="pharmacy.purchase-list"),
    re_path(r'^product/purchase-order-pending/$', views.PurchaseOrderPendingList.as_view(),
        name="pharmacy.purchase-purchase-order"),
    re_path(r'^product/purchase-order-completed/$', views.PurchaseOrderCompletedList.as_view(),
        name="pharmacy.purchase-purchase-order-completed"),
    re_path(r'^product/purchase-order-discarded/$', views.PurchaseOrderDiscardedList.as_view(),
        name="pharmacy.purchase-purchase-order-discarded"),
    re_path(r'^product/purchase-requisition/$', views.PurchaseRequisitionList.as_view(),
        name="pharmacy.purchase-requisition-list"),
    re_path(r'^product/purchase/(?P<alias>[\w-]+)/$',
        views.PurchaseDetails.as_view(), name="pharmacy.purchase-details"),
    re_path(r'^product/order-reports/$', views.PurchaseOrderReport.as_view(),
        name="pharmacy.purchase-order-report"),
    re_path(r'^product/purchase-requisition/(?P<alias>[\w-]+)/$',
        views.PurchaseRequisitionDetails.as_view(), name="pharmacy.purchase-requisition-details"),
    re_path(r'^product/purchase-requisition/(?P<alias>[\w-]+)/related/$', RequisitionRelatedPurchaseOrderProcurement.as_view(),
        name="pharmacy.product.purchase-requisition.related"),
    re_path(r'^product/sales-return/$', views.SalesReturnList.as_view(),
        name="pharmacy.sales-return-list"),
    re_path(r'^product/purchase-order/(?P<order_alias>[\w-]+)/rest/$',
        views.PurchaseOrderRestList.as_view(), name="pharmacy.purchase-order-rest"),
    re_path(
        r'^purchase-summary-report/$',
        views.PurchaseSummaryReport.as_view(),
        name="pharmacy.purchase-summary-report"
    ),
    re_path(
        r'^product-purchase-summary/$',
        views.ProductPurchaseSummary.as_view(),
        name="pharmacy.product-purchase-summary"
    ),
    re_path(r'^product/sales-return/(?P<alias>[\w-]+)/$',
        views.SalesReturnDetails.as_view(),
        name="pharmacy.sales-return.details"),

    re_path(r'^product/stock/$', views.StockList.as_view(), name="pharmacy.stock-list"),
    path(
        'distributor/stocks/<uuid:alias>/change-history/',
        StockChangeHistory.as_view(),
        name="distributor-stock-change-history"
    ),
    re_path(r'^product/stock/search/$', views.StockSearch.as_view(),
        name="pharmacy.stock-search"),

    re_path(r'^product/stock/transfer/$', views.StockTransferList.as_view(),
        name="pharmacy.stock-transfer"),
    re_path(r'^product/stock/transfer/requisition/$', views.StockTransferRequisitionList.as_view(),
        name="pharmacy.stock-transfer-requisition"),
    re_path(r'^product/stock/transfer/(?P<alias>[\w-]+)/$', views.StockTransferDetails.as_view(),
        name="pharmacy.stock-transfer-details"),
    re_path(r'^product/stock/expire/(?P<id>\d+)/(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})/$',
        views.StockIOExpiredList.as_view(), name="pharmacy.stock-list-expire"),
    re_path(r'^product/stock/(?P<alias>[\w-]+)/$', views.StockDetails.as_view(),
        name="pharmacy.stock-details"),
    re_path(r'^product/stock/(?P<alias>[\w-]+)/products/$', views.StockProductList.as_view(),
        name="pharmacy.stock-product-list"),
    re_path(r'^product/stock/(?P<alias>[\w-]+)/products/cache/$',
        StockProductCachedList.as_view(),
        name="pharmacy.stock-product-cache-list"),
    re_path(r'^product/stock/(?P<alias>[\w-]+)/products/sales-able/$',
        views.SalesAbleStockProductList.as_view(),
        name="pharmacy.sales-able-stock-product.list"),

    re_path(r'^product/stock/(?P<alias>[\w-]+)/products/sales-able/cache/$',
        SalesAbleStockProductCachedList.as_view(),
        name="pharmacy.sales-able-stock-product-cache.list"),
    path('product/fetch-by-stock-id/',
            ProductListFetchByStockId.as_view(),
            name='fetch-product-by-stock-id-list'),
    re_path(r'^distributor/stocks/products/$',
        DistributorSalesAbleStockProductList.as_view(),
        name="pharmacy.distributor-sales-able-stock-product.list"),
    re_path(r'^distributor/stocks/products/flash/$',
        DistributorSalesAbleStockFlashProductList.as_view(),
        name="pharmacy.distributor-sales-able-stock-product.list.flash"),
    re_path(r'^distributor/stocks/products/trending/$',
        DistributorSalesAbleStockTrendingProductList.as_view(),
        name="pharmacy.distributor-sales-able-stock-product.list.trending"),
    re_path(r'^distributor/stocks/products/recent/$',
        DistributorSalesAbleStockRecentOrderedProductList.as_view(),
        name="pharmacy.distributor-sales-able-stock-product.list.recent"),
    path('distributor/stocks/<uuid:alias>/similar-products/',
        DistributorSalesAbleStockSimilarProductList.as_view(),
        name="pharmacy.distributor-sales-able-stock-product.list.similar"),
    path('distributor/stocks/<uuid:alias>/recommended-products/',
        DistributorSalesAbleStockRecommendedProductList.as_view(),
        name="pharmacy.distributor-sales-able-stock-product.list.recommended"),
    path(
        'distributor/stocks/products/<uuid:alias>/',
        DistributorStockDetails.as_view(),
        name="distributor-stock-details"
    ),

    re_path(r'^product/opening-stock/$', views.ProductOpeningStockView.as_view(),
        name="product.opening-stock"),
    re_path(r'^product/stock/previous-info/(?P<stock_alias>[\w-]+)/$',
        views.StocksPreviousInfo.as_view(),
        name="stocks-previous-inventory-info"),

    re_path(r'^product/stock-io-log/$', views.StockIOList.as_view(),
        name="pharmacy.stock-io-log-list"),
    re_path(r'^product/stock-io-log/bulk/$', views.StockIOBulkCreate.as_view(),
        name="pharmacy.stock-io-log-bulk-create"),
    re_path(r'^product/stock-io-log/store/(?P<alias>[\w-]+)/(?P<product>[\w-]+)/$',
        views.StockIOListByStore.as_view(),
        name="pharmacy.stock-io-log-list-by-store"),
    re_path(r'^product/stock-io-log/(?P<alias>[\w-]+)/$', views.StockIODetails.as_view(),
        name="pharmacy.stock-io-log-details"),
    re_path(r'^product/report/stock-io-log/$',
        views.StockIOReport.as_view(), name="pharmacy.stock-io-log-report"),
    re_path(r'^product/report/inventory-summary/$',
        views.InventorySummary.as_view(), name="pharmacy.inventory-summary-report"),
    re_path(r'^possible-duplicate-product/$', views.PossibleDuplicateProductList.as_view(), name="pharmacy.possible-duplicate-product.list"),

    re_path(r'^product/$', views.ProductList.as_view(), name="pharmacy.product.list"),
    re_path(r'^discarded-product/$', views.DiscardedProductList.as_view(), name="pharmacy.discarded_product.list"),
    re_path(r'^product/stock-under-demand/$', views.ProductStockUnderDemand.as_view(),
        name="pharmacy.product-list-stock-inder-demand"),
    # re_path(r'^product/search/$', views.ProductSearch.as_view(),
    #     name="pharmacy.product.search"),
    # re_path(r'^product/medicine/search/$', views.ProductMedicineSearch.as_view(),
    #     name="pharmacy.product.medicine.search"),
    re_path(r'^product/(?P<alias>[\w-]+)/batch/search/$',
        views.BatchSearch.as_view(), name="pharmacy.product-batch-search"),
    re_path(r'^product/batch/search/$',
        views.AllBatchSearch.as_view(), name="pharmacy.all-product-batch-search"),
    re_path(r'^product/(?P<alias>[\w-]+)/stock/$', views.ProductStockList.as_view(),
        name="pharmacy.product-stock-list"),
    re_path(
        r'^product/merge/$',
        views.ProductMerge.as_view(),
        name="product-merge"
    ),
    re_path(r'^unit/merge/$', views.UnitMerge.as_view(), name="unit-merge"),
    re_path(r'^product/(?P<alias>[\w-]+)/$', views.ProductDetails.as_view(),
        name="pharmacy.product.details"),

    re_path(r'^storepoint/$', views.StorePointList.as_view(),
        name="pharmacy.storepoint.list"),
    # this re_path is already exists in search app
    # re_path(r'^storepoint/search/$', views.StorePointSearch.as_view(),
    #     name="pharmacy.storepoint.search"),
    re_path(r'^storepoint/(?P<alias>[\w-]+)/$', views.StorePointDetails.as_view(),
        name="pharmacy.storepoint.details"),
    re_path(r'^employee-storepoint/$', views.EmployeeStorePointAccessList.as_view(),
        name="pharmacy.employee-storepoint-access.list"),
    re_path(r'^employee-storepoints/(?P<alias>[\w-]+)/$',
        views.EmployeeStorePointDetails.as_view(),
        name="pharmacy.employee-storepoint.details"),
    re_path(r'^employee-storepoint/(?P<employee_alias>[\w-]+)/$',
        views.EmployeeStorePointList.as_view(),
        name="pharmacy.employee-storepoint.list"),
    re_path(r'^employee-storepoint/(?P<employee_alias>[\w-]+)/all/$',
        views.EmployeeAllStorePointList.as_view(),
        name="pharmacy.employee-storepoint.list-all"),
    re_path(r'^employee-accounts/(?P<alias>[\w-]+)/$',
        views.EmployeeAccountDetails.as_view(),
        name="pharmacy.employee-account.details"),
    re_path(r'^employee-account/(?P<employee_alias>[\w-]+)/$',
        views.EmployeeAccountList.as_view(),
        name="pharmacy.employee-account.list"),
    re_path(r'^employee-account/(?P<employee_alias>[\w-]+)/all/$',
        views.EmployeeAllAccountList.as_view(),
        name="pharmacy.employee-all-account.list"),
    re_path(r'^product/stock/product-batchwise/(?P<product>\d+)/$',
        views.StockIOListProductBatchWise.as_view(), name="pharmacy.product-batchwise"),
    re_path(r'^product/stock/storepoint-batchwise/(?P<store>\d+)/$',
        views.StockIOListStorePointBatchWise.as_view(), name="pharmacy.stock-list-batchwise"),
    re_path(r'^product/stock/storepoint-batchwise/(?P<store>\d+)/(?P<product>\d+)/$',
        views.StockIOListStorePointProductBatchWise.as_view(),
        name="pharmacy.stock-list-product-batchwise"),
    re_path(
        r'^product/stock/storepoint-batchwise/(?P<store>\d+)/'
        r'(?P<product>\d+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$',
        views.StockIOListStorePointProductBatchDateWise.as_view(),
        name="pharmacy.stock-list-product-batchwise-date"),
    re_path(r'^stock-reports/$', views.StockReport.as_view(),
        name="pharmacy.stock-report"),
    re_path(r'^product-last-usage/$', views.ProductLastUsageDate.as_view(),
        name="pharmacy.product-last-usage"),
    re_path(r'^stock-details-reports/$', views.StockDetailsReport.as_view(),
        name="pharmacy.stock-details-report"),
    re_path(r'^product-stock-summary/$', views.ProductStockSummaryReport.as_view(),
        name="pharmacy.product-stock-report"),
    re_path(r'^stock-adjustments/$', views.StockAdjustmentList.as_view(),
        name="pharmacy.stock-adjustments"),
    re_path(r'^stock-adjustments/(?P<alias>[\w-]+)/$', views.StockAdjustmentDetails.as_view(),
        name="pharmacy.stock-adjustment.details"),
    re_path(r'^stock-disbursements/$', views.StockDisbursementList.as_view(),
        name="pharmacy.stock-disbursements"),
    re_path(r'^ordered-product-stock/(?P<store_alias>[\w-]+)/(?P<order_alias>[\w-]+)/$',
        views.StorePointProductStockList.as_view(),
        name="pharmacy.ordered-product-stock"),
    re_path(r'^unit/$', views.UnitList.as_view(),
        name="pharmacy.unit-list"),
    re_path(r'unit/(?P<alias>[\w-]+)/$', views.UnitDetails.as_view(),
        name="pharmacy.unit-details"),
    re_path(r'^product-disbursement-cause/$', views.ProductDisbursementCauseList.as_view(),
        name="pharmacy.product-disbursement-cause-list"),
    re_path(r'^product-disbursement-cause/(?P<alias>[\w-]+)/$',
        views.ProductDisbursementCauseDetails.as_view(),
        name="pharmacy.product-disbursement-cause-details"),
    re_path(
        r'^report/product-short-report/$',
        views.ProductShortList.as_view(),
        name="pharmacy.product-short-report"),
    re_path(
        r'^sales/graph/store-wise/$',
        views.StoreWiseSalesGraphData.as_view(),
        name="pharmacy.sales.graph.store-wise"),
    re_path(
        r'^sales/graph/store-wise/amount/$',
        views.StoreWiseSalesAmountGraphData.as_view(),
        name="pharmacy.sales.graph.store-wise.amount"),
    re_path(
        r'^sales/graph/company-wise/$',
        views.CompanyWiseSalesGraphData.as_view(),
        name="pharmacy.sales.graph.company-wise"),
    re_path(r'^report/sales/hourly/$', views.GetHourlySalesAttributeList.as_view(),
        name="pharmacy.hourly-sales-report"),
    re_path(
        r'^store-wise-stock-value/$',
        views.StoreWiseStockValue.as_view(),
        name="pharmacy.store-wise-stock-value"
    ),
    re_path(
        r'^stock-bulk-update/$',
        views.StockBulkUpdate.as_view(),
        name="pharmacy.stock-bulk-update"
    ),
    # Reports
    re_path(
        r'^reports/sales-purchase-stock-value-summary/group-wise/$',
        SalesPurchaseStockValueGroupWiseSummary.as_view(),
        name="sales-purchase-stock-value-group-wise-summary"
    ),
    re_path(
        r'^reports/distributor-order-product-summary/$',
        DistributorOrderProductSummary.as_view(),
        name="distributor-order-product-summary"
    ),
    re_path(
        r'^reports/productwise-distributor-order-discount-summary/(?P<stock_alias>[\w-]+)/$',
        ProductWiseDistributorOrderDiscountSummary.as_view(),
        name="productwise-distributor-order-discount-summary"
    ),
    re_path(
        r'^reports/productwise-distributor-order-discount-summary/$',
        ProductWiseDistributorOrderDiscountSummary.as_view(),
        name="productwise-distributor-order-discount-summary"
    ),
    re_path(
        r'^reports/date-status-wise-order-amount/$',
        DateAndStatusWiseOrderAmount.as_view(),
        name="date-status-wise-order-amount"
    ),
    re_path(
        r'^reports/delivery-sheet/responsible-employee-wise/$',
        ResponsibleEmployeeWiseDeliverySheetList.as_view(),
        name="responsible-employee-wise-delivery-sheet"
    ),
    re_path(
        r'^reports/stock-transfer/$',
        ProductWiseStockTransferReport.as_view(),
        name="stock-transfer-report"
    ),
    re_path(
        r'^reports/mismatched-stocks/$',
        MismatchedStockWithIOProductList.as_view(),
        name="mismatched-stock-report"
    ),
    # SU Reports
    re_path(
        r'^su-reports/distributor-order-summary/$',
        DistributorOrganizationOrderSummary.as_view(),
        name="distributor-order-summary"
    ),
    # Purchase Prediction
    re_path(
        r'^prediction/purchase/$',
        PurchasePrediction.as_view(),
        name="purchase-prediction"
    ),
    re_path(
        r'^adv-prediction/purchase/$',
        AdvPurchasePrediction.as_view(),
        name="adv-purchase-prediction"
    ),
    re_path(
        r'^stock/writing/$',
        StockWritingFormat.as_view(),
        name="stock-writing-format"
    ),
    re_path(
        r'^log/order/$',
        OrderDetails.as_view(),
        name="details_of_a_order"
    ),
    # Lossing Item
    re_path(
        r'^prediction/purchase/loss/$',
        LossProduct.as_view(),
        name="purchase-loss"
    ),
    # Supplier product received
    re_path(
        r'^supplier/purchase/products/received/$',
        PurchaseSupplierProductReceivedHistory.as_view(),
        name="supplier-product-received"
    ),

    re_path(
        r'^supplier/purchase/products/history/$',
        SupplierPurchaseHistory.as_view(),
        name="supplier-product-purchase-history"
    ),

    # Distributor Order Purchase Prediction
    re_path(
        r'^prediction/order/purchase/$',
        DistributorOrderPurchasePrediction.as_view(),
        name="distributor-order-purchase-prediction"
    ),
    # Organization Invoice History
    re_path(
        r'^organization/order/invoice/history/$',
        OrganizationOrderInvoiceHistory.as_view(),
        name="organization-order-invoice-history"
    ),
    # Purchase Supplier Invoice Product History
    re_path(
        r'^purchase/supplier/invoice/product-history/$',
        PurchaseSupplierInvoiceProductHistory.as_view(),
        name="purchase-supplier-invoice-product-history"
    ),
    # Distributor order related re_paths
    re_path(
        r'^distributor/order/cart/$',
        DistributorOrderCartListCreate.as_view(),
        name="distributor-order-cart-list-create"
    ),
    re_path(
        r'^distributor/order/reorder/$',
        DistributorReOrder.as_view(),
        name="distributor-order-re-order"
    ),
    re_path(
        r'^distributor/order/tracking/$',
        OrderTrackingList.as_view(),
        name="distributor-order-tracking-list-create"
    ),
    re_path(
        r'^distributor/product/order-limit/(?P<stock_alias>[\w-]+)/$',
        views.DistributorOrderLimitPerDay.as_view(),
        name="distributor-product-order-limit"
    ),
    re_path(
        r'^distributor/order/clone/$',
        OrderClone.as_view(),
        name="order-clone"
    ),
    re_path(
        r'^distributor/order/(?P<alias>[\w-]+)/$',
        DistributorOrderDetails.as_view(),
        name="distributor-order-details"
    ),
    re_path(
        r'^distributor/order/$',
        DistributorOrderListCreate.as_view(),
        name="distributor-order-list-create"
    ),
    path(
        "distributor/non-grouped/orders/",
        DistributorNonGroupedOrderList.as_view(),
        name="distributor-non-grouped-orders"
    ),
    path(
        'distributor/order/status-change-log/<uuid:alias>/',
        DistributorOrderStatusChangeLogList.as_view(),
        name="distributor-order-status-change-log-list"
    ),
    re_path(
        r'^distributor/order-stats/$',
        DistributorOrderStats.as_view(),
        name="distributor-order-stats"
    ),
    re_path(
        r'^distributor/order/status-responsible-person/bulk/create/$',
        OrderStatusResponsiblePersonBulkCreate.as_view(),
        name="distributor-order-status-responsible-person-bulk-create"
    ),
    re_path(
        r'^distributor/order/accept/bulk/$',
        OrderBulkStatusUpdate.as_view(),
        name="distributor-order-bulk-accept"
    ),
    re_path(
        r'^ecommerce/order/processing-items/$',
        ProcessingToDeliverStockList.as_view(),
        name="distributor-order-processing-item-list"
    ),
    # Generate PDF
    re_path(
        r'^order/invoice/generate-pdf/$',
        GeneratePdfInvoice.as_view(),
        name="generate-invoice-pdf"
    ),
    re_path(
        r'^order/pdf-invoice-list/$',
        OrderPdfInvoiceList.as_view(),
        name="order-pdf-invoice-list"
    ),
    #invoice status change log
    re_path(
        r'^invoice-status-change-log/$',
        InvoiceStatusChangeLog.as_view(),
        name="invoice-status-change-log"
    ),
    path(
        'get-discount-rules/',
        GetDiscountRules.as_view(),
        name='get-discount-rules'
    ),
    path(
        'order/tracking/status-change-log/',
        OrderTrackingStatusChangeLog.as_view(),
        name="order-tracking-status-change-log"
    ),
    path(
        'distributor/stocks/products/get-sorting-options/',
        GetProductSortingOptions.as_view(),
        name="get-product-sorting-options"
    ),
    path(
        'order/cancel-from-customer-end/<uuid:order_alias>/',
        CancelOrderFromCustomerEnd.as_view(),
        name="cancel-order-from-customer-end"
    ),
    path(
        'product-bulk-update/',
        ProductPropertiesBulkUpdate.as_view(),
        name="product-properties-bulk-update"
    ),
    path(
        'product-restock-reminder/',
        ProductRestockReminderListCreate.as_view(),
        name="product-restock-reminder-list-create"
    ),
    path(
        'product-restock-reminder/<uuid:alias>/',
        ProductRestockReminderUpdate.as_view(),
        name="product-restock-reminder-list-create"
    ),
    path(
        'product-restock-reminder/items/',
        OrganizationWiseProductRestockReminderList.as_view(),
        name="organization-wise-product-restock-reminder-list"
    ),
    path(
        'orders-graph/',
        OrderPreOrderGraphList.as_view(),
        name="orders-graph"
    ),
    path(
        "damage-products/",
        DamageProductList.as_view(),
        name="damage-product-list"
    ),
    path(
        "damage-products/<uuid:alias>/",
        DamageProductDetail.as_view(),
        name="damage-product-detail"
    ),
    path(
        "recheck-products/",
        RecheckProductList.as_view(),
        name="recheck-product-list"
    ),
    path(
        "recheck-products/<uuid:alias>/",
        RecheckProductDetail.as_view(),
        name="recheck-product-detail"
    ),
    path(
        "damage-items/",
        DamageItemsList.as_view(),
        name="damage-items-list",
    ),
    path("recheck-items/",
        RecheckItemsList.as_view(),
        name="recheck-item-list"
    ),
    path("recheck-items/<uuid:alias>/",
         RecheckItemsDetail.as_view(),
         name="recheck-item-detail"
    ),
]
