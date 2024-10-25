from django.urls import path, include

urlpatterns = [
    path(
        "/manufacturer/",
        include("search.url.manufacturer")
    ),
]
