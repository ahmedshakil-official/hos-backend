from django.urls import re_path
from ..views.person import (
    EmployeeList,
    EmployeeDetails,
    PorterFromReporterCreate
)
from django.urls import path
from ..views import employee_manager

urlpatterns = [
    path(
        'managers/',
        employee_manager.EmployeeManagerList.as_view(),
        name="employee-manager-list"
    ),
    path(
        'managers/<uuid:alias>/',
        employee_manager.EmployeeManagerDetails.as_view(),
        name="employee-manager-details"
    ),
    path(
        'get-manager-by-code/',
        employee_manager.GetManagerByEmployeeCode.as_view(),
        name="get-manager-by-employee-code"
    ),
    re_path(
        r"^(?P<alias>[\w-]+)/$",
        EmployeeDetails.as_view(),
        name="employee-details",
    ),
    path(
        "porter/create/", 
        PorterFromReporterCreate.as_view(), 
        name="porter-create"
    ),
    re_path(r"^$", EmployeeList.as_view(), name="employee-list"),
]
