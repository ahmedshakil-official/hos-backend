from django.urls import path

from ..views.short_return_log import (
    ShortReturnLogListCreate,
    ShortReturnLogListItemWise,
    ApproveShortReturns,
    ShortReturnLogRetrieveUpdateDestroy,
    ShortLogList, ReturnLogList
)
from ..views.short_return_item import ReturnReportList

urlpatterns = [

    path(
        'short-return/',
        ShortReturnLogListCreate.as_view(),
        name='short-return-list'

    ),

    path(
        'short-return/item-wise/',
        ShortReturnLogListItemWise.as_view(),
        name='short-return-list-item-wise'

    ),
    path(
        'delivery-sheet/short-return/approve/',
        ApproveShortReturns.as_view(),
        name='delivery-sheet-approve-short-returns'

    ),
    path(
        'short-return/<uuid:alias>/',
        ShortReturnLogRetrieveUpdateDestroy.as_view(),
        name='short-return-list-details'

    ),
    path(
        'shorts/',
        ShortLogList.as_view(),
        name='short-return-list'

    ),
    path(
        'returns/',
        ReturnLogList.as_view(),
        name='short-return-list'

    ),
    path(
        'return-list/product-wise/export-as-xlxs/',
        ReturnReportList.as_view(),
        name='short-return-list-by-product'
    )

]
