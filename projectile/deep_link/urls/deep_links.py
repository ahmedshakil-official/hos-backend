"""URLs mappings for Deep Links"""

from django.urls import path

from deep_link.views.deep_links import DeepLinkList


urlpatterns = [
    path("", DeepLinkList.as_view(), name='deep-link-list-create'),
]
