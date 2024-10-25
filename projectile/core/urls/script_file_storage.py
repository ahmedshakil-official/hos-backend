from django.urls import re_path
from ..views.script_file_storage import (
    ScriptFileStorageList,ScriptFileStorageDetails
)

urlpatterns = [
    re_path(
        r'^files/(?P<alias>[\w-]+)/$',
        ScriptFileStorageDetails.as_view(),
        name="script-related-file-details"
    ),
    re_path(
        r'^files/$',
        ScriptFileStorageList.as_view(),
        name="script-related-file-upload"
    ),
]
