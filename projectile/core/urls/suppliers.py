from django.urls import re_path
from ..views.person import (
    SupplierList, SupplierDetails
)

urlpatterns = [
    re_path(r'^(?P<alias>[\w-]+)/$',
        SupplierDetails.as_view(), name="supplier-details"),
    re_path(r'^$', SupplierList.as_view(), name="supplier-list"),
]
