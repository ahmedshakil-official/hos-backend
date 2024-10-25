from django.urls import re_path

from ..views.person_organization import (
    PersonOrganizationSupplierDetails, PersonOrganizationSupplierList, PersonOrganizationEmployeeList, PersonOrganizationEmployeeDetails
)

urlpatterns = [
    re_path(
        r'^suppliers/(?P<alias>[\w-]+)/$',
        PersonOrganizationSupplierDetails.as_view(),
        name="person-organization-supplier-details"
    ),
    re_path(
        r'^suppliers/$',
        PersonOrganizationSupplierList.as_view(),
        name="person-organization-supplier-list"
    ),
    re_path(r'^employees/$',
        PersonOrganizationEmployeeList.as_view(),
        name="person-organization-employee-list"),
    re_path(
        r'^employees/(?P<alias>[\w-]+)/$',
        PersonOrganizationEmployeeDetails.as_view(),
        name="person-organization-employee-details"
    ),
]
