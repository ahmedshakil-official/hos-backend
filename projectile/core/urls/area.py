"""URLs Mapping for area."""

from django.urls import path

from core.views.area import (
    AreaList,
    AreaDetail,
    AreaBulkUpdate,
)

urlpatterns = [
    path(
        "",
        AreaList.as_view(),
        name="area-list-create"
    ),
    path(
        "<uuid:alias>/",
        AreaDetail.as_view(),
        name="area-details"
    ),
    path(
        "bulk-update/",
        AreaBulkUpdate.as_view(),
        name="area-bulk-update"
    ),
]
