from django.urls import re_path
from ..views.person_organization import ContractorList, ContractorDetails

urlpatterns = [
    re_path(
        r"^(?P<alias>[\w-]+)/$", ContractorDetails.as_view(), name="contractor-details"
    ),
    re_path(r"^$", ContractorList.as_view(), name="contractor-list"),
]
