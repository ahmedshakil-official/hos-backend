from django.urls import re_path
from django.urls import path
from ..views import issue

urlpatterns = [
    path('', issue.IssueList.as_view(), name="issue-list"),
    re_path(r'^status/$', issue.IssueStatusList.as_view(), name="issue-status-list"),
    re_path(r'^(?P<alias>[\w-]+)/$', issue.IssueDetails.as_view(), name="issue-details"),
]