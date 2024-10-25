from django.urls import re_path
from ..views.department import (
    DepartmentList, DepartmentSearch, DepartmentDetails
)
urlpatterns = [
    re_path(r'^$', DepartmentList.as_view(), name="department-list"),
    re_path(r'^search/$', DepartmentSearch.as_view(),
        name="department-search"),
    re_path(r'^(?P<alias>[\w-]+)/$',
        DepartmentDetails.as_view(), name="department-details"),
]

