from django.urls import path

from .views.prediction_item import (
    PredictionItemList, DownloadPredictionData,
    PredictionItemDetails, GetInvoiceNumberForProcure
)
from .views.procure import (
    ProcureListCreate,
    ProcureDetails,
    CompletePurchase,
    ProcureChangeLog,
    ProcureStatusLog,
    ProcureGroupStatusLog,
    ProcureHistory,
    ProcureDateUpdate,
    ProcureCreditBulkUpdate,
)
from .views.procure_group import (
    ProcureGroupListCreate, ProcureGroupDetails,
    ProcureGroupStatusChange, ProcureGroupCompletePurchase,
    ProcureGroupEdit, ProcureInfoReport
)
from .views.procure_issue_log import ProcureIssueListCreate
from .views.procure_payment import (
    ProcurePaymentLog,
    ProcurePaymentList,
    ProcurePaymentDetail,
    BulkCreateProcurePaymentView
)
from .views.purchase_prediction import (
    PurchasePredictionListCreate,
    PurchasePredictionIsLockedUpdate,
    PopulatePurchasePredictionDataFromPredFile,
)
from .views.procure_status import ProcureStatusListCreate
from .views.prediction_item_supplier import PredictionItemSupplierInfo
from .views.prediction_item_mark import PredictionItemMarkListCreate
from .views.reports import (
    ProcurementReportProductWise,
    PredictionNotProcuredItemsReport,
    GenerateProcuresInfoReport,
    GenerateProcuresInfoSummary,
    PurchaseReportDateWise,
)
from .views.common import ProcurementShopList
from procurement.views.procure_return import (
    ProcureReturnList,
    ProcurePurchaseListProductContractorWise,
    ProcureReturnDetail,
    ProcureReturnSettlementLog,
    ReturnSettlementDetail,
    ReturnSettlementList,
)

# pylint: disable=invalid-name
urlpatterns = [
    path('purchase/prediction-items/', PredictionItemList.as_view(), name='prediction-item-list'),
    path('purchase/prediction-items/<uuid:alias>/', PredictionItemDetails.as_view(), name='prediction-item-details'),
    path('procures/', ProcureListCreate.as_view(), name='procure-list-create'),
    path('procure-status/', ProcureStatusListCreate.as_view(), name='procure-status-list-create'),
    path('procures/<uuid:alias>/', ProcureDetails.as_view(), name="procure-details"),
    path('procures/requisition-order-purchase/', CompletePurchase.as_view(), name='complete-purchase'),
    path('procures/issues/', ProcureIssueListCreate.as_view(), name='procure-issue-list-create'),
    path('purchase/predictions/', PurchasePredictionListCreate.as_view(), name='purchase-prediction-list-create'),
    path('purchase/predictions/<uuid:alias>/lock-update/', PurchasePredictionIsLockedUpdate.as_view(), name='purchase-prediction-is-locked-update'),
    path('populate-prediction-data/', PopulatePurchasePredictionDataFromPredFile.as_view(), name='purchase-prediction-list-create'),
    path('prediction-item-supplier/info/', PredictionItemSupplierInfo.as_view(), name='prediction-supplier-info'),
    path('prediction-item/mark/', PredictionItemMarkListCreate.as_view(), name='prediction-item-mark'),
    path('report/procure/product-wise/', ProcurementReportProductWise.as_view(), name='procure-report-product-wise'),
    path('shop-names/', ProcurementShopList.as_view(), name='procure-shop-name-list'),
    path(
        'report/prediction/<uuid:alias>/not-procured/',
        PredictionNotProcuredItemsReport.as_view(),
        name='prediction-not-procured-items'
    ),
    path(
        'report/prediction/download/',
        DownloadPredictionData.as_view(),
        name='create-prediction-data'
    ),
    path(
        'report/procurement-purchase-info/',
        PurchaseReportDateWise.as_view(),
        name='procurement-purchase-info-date-wise',
    ),
    path(
        'procures/info/report/',
        GenerateProcuresInfoReport.as_view(),
        name="generate-procures-data"
    ),
    path(
        'procures/info/summary/',
        GenerateProcuresInfoSummary.as_view(),
        name="generate-procures-data-message"
    ),
    path(
        'procures/next-invoice-number/',
        GetInvoiceNumberForProcure.as_view(),
        name="get-invoice-number-for-creating-procure"
    ),
    path(
        'procures/groups/',
        ProcureGroupListCreate.as_view(),
        name="procure-group-list-create"
    ),
    path(
        'procures/groups/<uuid:alias>/',
        ProcureGroupDetails.as_view(),
        name="procure-group-details"
    ),
    path(
        'procures/groups/status/',
        ProcureGroupStatusChange.as_view(),
        name="procure-group-status-change"
    ),
    path(
        'procures/groups/complete-purchase/',
        ProcureGroupCompletePurchase.as_view(),
        name="procure-group-complete-purchase"
    ),
    path(
        'procures/groups/edit/',
        ProcureGroupEdit.as_view(),
        name="procure-group-edit"
    ),
    path(
        'procures/change-log/<uuid:alias>/',
        ProcureChangeLog.as_view(),
        name="procure-change-log"
    ),
    path(
        "procures/status-log/<uuid:alias>/",
        ProcureStatusLog.as_view(),
        name="procure-status-log"
    ),
    path(
        "procures/groups/status-log/<uuid:alias>/",
        ProcureGroupStatusLog.as_view(),
        name="procure-group-status-log"
    ),
    path(
        "procures/returns/",
        ProcureReturnList.as_view(),
        name="procures-returns-list-create"
    ),
    path(
        "procures/returns/<uuid:alias>/",
        ProcureReturnDetail.as_view(),
        name="procures-returns-detail"
    ),
    path(
        "procures/returns-settlements/log/<uuid:alias>/",
        ProcureReturnSettlementLog.as_view(),
        name="procure-returns-settlements-log-details",
    ),
    path(
        "procures/returns/settlement/<uuid:alias>/",
        ReturnSettlementDetail.as_view(),
        name="procures-returns-settlement-detail"
    ),
    path(
        "procures/product-contractor-purchases/",
        ProcurePurchaseListProductContractorWise.as_view(),
        name="procure-purchaseL-list-product-contractor-wise"
    ),
    path(
        "procures/returns/settlements/",
        ReturnSettlementList.as_view(),
        name="procure-return-settlements"
    ),
    path(
        "procures/payments/",
        ProcurePaymentList.as_view(),
        name="procure-payments"
    ),
    path("procure-payments/bulk-create/",
         BulkCreateProcurePaymentView.as_view(),
         name='bulk-create-procure-payment'),
    path(
        "procures/payments/<uuid:alias>/",
        ProcurePaymentDetail.as_view(),
        name="procure-payments-detail"
    ),
    path(
        "procures/payments/<uuid:alias>/log/",
        ProcurePaymentLog.as_view(),
        name="procure-payment-history",
    ),
    path(
        "procures/log/<uuid:alias>/",
        ProcureHistory.as_view(),
        name="procure-history"
    ),
    path(
        "procure/date/update/",
        ProcureDateUpdate.as_view(),
        name="procure-date-update"
    ),
    path(
        "procure-credits/bulk-update/",
        ProcureCreditBulkUpdate.as_view(),
        name="procure-credit-bulk-update",
    ),
    path(
        "procure/info/report/",
        ProcureInfoReport.as_view(),
        name="procure-info-report",
    )
]
