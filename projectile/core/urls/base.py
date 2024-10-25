# from .common import urlpatterns as url_common
from django.urls import re_path

from django.urls import path, include
from ..views.common import CountryList, DateFormatList, DeliveryAreaList
from ..views.organizations import DistributorBuyerOrganizationMerge
from ..views import public
from ..views.organization import OrganizationPossiblePrimaryResponsiblePerson
from ..views.person import (
    PersonAccessOrganizationList,
    UserPhoneNumberUpdate,
    UserPasswordResetList,
    UserPasswordResetByCustomerCareService,
    UserSoftDelete,
)

urlpatterns = [
    path("person-organization/", include("core.urls.person_organization"),
        name="person_organization"),
    path("department/", include("core.urls.department"), name="department"),
    path("script/", include("core.urls.script_file_storage"),
        name="script_file_storage"),
    path("designation/", include("core.urls.designation"), name="designation"),
    path("organizations/", include("core.urls.organizations"), name="organizations"),
    path("reports/", include("core.urls.reports"), name="reports"),
    path("traders/", include("core.urls.traders"), name="traders"),
    path("contractors/", include("core.urls.contractors"), name="contractors"),
    path("issues/", include("core.urls.issues"), name="issues"),
    path("employee/", include("core.urls.employee"), name="employee"),
    path("suppliers/", include("core.urls.suppliers"), name="suppliers"),
    # common urls
    re_path(r"^country/$", CountryList.as_view(), name="country-list"),
    re_path(r"^date-format/$", DateFormatList.as_view(), name="date_format-list"),
    re_path(r"^areas/$", DeliveryAreaList.as_view(), name="delivery-area-list"),
    re_path(
        r"^buyer-organization/merge/$",
        DistributorBuyerOrganizationMerge.as_view(),
        name="buyer-organization-merge",
    ),
    re_path(
        r"^ecom/register/$",
        public.EcomUserRegistration.as_view(),
        name="e-cimmerce-user-registration",
    ),
    re_path(r"^auth/log/$", public.AuthLog.as_view(), name="auth-log"),
    re_path(
        r"^(?P<person_alias>[\w-]+)/organizations/$",
        PersonAccessOrganizationList.as_view(),
        name="person-access-organization-list",
    ),
    re_path(
        r'organization/sub-areas/$',
        public.OrganizationSubAreaList.as_view(),
        name="organization-sub-area-list"
    ),
    path(
        'organization/possible-primary-responsible-person/',
        OrganizationPossiblePrimaryResponsiblePerson.as_view(),
        name="organization-possible-primary-responsible-person"
    ),
    path(
        "phone-number/change/<uuid:alias>/",
        UserPhoneNumberUpdate.as_view(),
        name="users-phone-number-change-by-admin-or-telemarketer"
    ),
    path(
        "password-reset/request/",
        UserPasswordResetList.as_view(),
        name="users-password-reset-requests"
    ),
    path(
        "password-reset/<uuid:alias>/",
        UserPasswordResetByCustomerCareService.as_view(),
        name="users-password-reset-by-customer-care-service"
    ),
    path(
        "soft-delete/",
         UserSoftDelete.as_view(),
         name="users-soft-delete"
    ),
]
