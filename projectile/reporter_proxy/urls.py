from django.urls import path

from reporter_proxy.views.base import (
    ReporterProxyView,
)


urlpatterns = [
    path(
        "users/",
        ReporterProxyView.as_view(source="api/v1/users"),
        name="reporter-user-list",
    ),
    path(
        "users/create/",
        ReporterProxyView.as_view(source="api/v1/users/create"),
        name="reporter-user-create",
    ),
]
