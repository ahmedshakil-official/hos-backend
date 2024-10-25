from django.urls import re_path, path

from ..views import public, private
from core.views.password_reset import PasswordResetList, UserPasswordReset

urlpatterns = [
    # site re_path
    re_path(r'^password-reset/request/$', public.PasswordResetRequest.as_view(), name="password-reset-request"),
    re_path(r'^login/$', private.MeLogin.as_view(), name="login"),
    re_path(r'^logout/$', private.MeLogout.as_view(), name="logout"),
    re_path(r'^$', private.UserProfileDetail.as_view(), name="me-details"),
    re_path(r'^password/reset/request/$', PasswordResetList.as_view(), name="password-reset-request-list-create"),
    path('password/reset/', UserPasswordReset.as_view(), name="password-reset"),
]
