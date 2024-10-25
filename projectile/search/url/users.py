from django.urls import re_path
from ..view.users import (
    DepartmentSearchView,
    # EmployeeSearchView,
    EmployeeDesignationSearchView,
    OrganizationSearchView,
    PersonOrganizationSupplierSearchView,
    # UserSearchView,
    PersonOrganizationSearchView,
    EmployeeSupplierPersonOrganizationSearchView,
    PersonOrganizationEmployeeSearchView,
    PersonOrganizationContractorSearchView,
)

urlpatterns = [
    re_path(r'^department/$', DepartmentSearchView.as_view(), name="department-search"),
    # re_path(r'^employee/$', EmployeeSearchView.as_view(), name="employee-search"),
    re_path(
        r'^person-organization/employee-supplier/$',
        EmployeeSupplierPersonOrganizationSearchView.as_view(),
        name="person-organization-employee-supplier-search"
    ),
    re_path(r'^designation/$', EmployeeDesignationSearchView.as_view(),
        name="employee-designation-search"),
    re_path(
        r'^person-organization/suppliers/$',
        PersonOrganizationSupplierSearchView.as_view(),
        name="person-organization-supplier-search"
    ),
    re_path(
        r'^organizations/$', OrganizationSearchView.as_view(),
        name="organization-search"
    ),
    # re_path(r'^$', UserSearchView.as_view(), name="user-search"),

    re_path(r'^person-organization/$', PersonOrganizationSearchView.as_view(),
        name="organization-user-search"),
    re_path(r'^person-organization/employees/$',
        PersonOrganizationEmployeeSearchView.as_view(),
        name="person-organization-employee-search"),

    re_path(r'^person-organization/contractors/$',
        PersonOrganizationContractorSearchView.as_view(),
        name="person-organization-employee-search"),
]
