from django.urls import re_path
from ..view.procures import ProcureSearchView

urlpatterns = [
    re_path(
        r"^procures/$", ProcureSearchView.as_view(), name="procure-search"
    ),
]
