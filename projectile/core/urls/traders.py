from django.urls import re_path
from ..views.person_organization import (
    TraderList, TraderDetails
)

urlpatterns = [
    re_path(r'^(?P<alias>[\w-]+)/$',
        TraderDetails.as_view(), name="trader-details"),
    re_path(r'^$', TraderList.as_view(), name="trader-list"),
]