from django.urls import re_path
from .views import DroppedPharmacyList


urlpatterns = [
    re_path(
        r'^dropped-pharmacies-list$',
        DroppedPharmacyList.as_view(),
        name="notebookapi.dropped-pharmacy-list"
    ),
]
