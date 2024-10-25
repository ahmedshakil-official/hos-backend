from django.urls import re_path
from ..views.department import (
    EmployeeDesignationList, EmployeeDesignationDetails, EmployeeDesignationByDepartment
)

urlpatterns = [
    re_path(r'^$', EmployeeDesignationList.as_view(),
        name="designation-list"),
    # re_path(r'^search/$',
    #     users.EmployeeDesignationSearch.as_view(), name="designation-search"),
    re_path(r'^(?P<alias>[\w-]+)/$',
        EmployeeDesignationDetails.as_view(), name="designation-details"),
    re_path(r'^department/(?P<alias>[\w-]+)/$', EmployeeDesignationByDepartment.as_view(),
        name="designation-by-department-details"),
]
