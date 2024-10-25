from typing import TypeVar
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.models import TokenUser
from rest_framework_simplejwt.utils import get_md5_hash_password

from common.cache_keys import AUTH_USER_CACHE_KEY_PREFIX


AuthUser = TypeVar("AuthUser", AbstractBaseUser, TokenUser)
USER_CACHE_TIMEOUT = 86400
USER_ONLY_FIELDS = [
    'id',
    'first_name',
    'last_name',
    'phone',
    'email',
    'alias',
    'is_superuser',
    'organization',
    'is_staff',
    'password',
    'person_group',
    'status',
    'is_active',
]

class CustomJWTAuthentication(JWTAuthentication):
    def get_auth_user_cache_key(self, user_id):
        return f"{AUTH_USER_CACHE_KEY_PREFIX}{user_id}"

    def get_user_from_cache(self, user_id):
        cache_key = self.get_auth_user_cache_key(user_id)
        user = cache.get(cache_key)
        return user

    def get_user(self, validated_token: Token) -> AuthUser:
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        user = self.get_user_from_cache(user_id)
        # Get the user from DB if no cache found
        if not user:
            try:
                user = self.user_model.objects.only(*USER_ONLY_FIELDS).get(**{api_settings.USER_ID_FIELD: user_id})
                cache.set(self.get_auth_user_cache_key(user_id), user, USER_CACHE_TIMEOUT)
            except self.user_model.DoesNotExist:
                raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        if api_settings.CHECK_REVOKE_TOKEN:
            password_hash = validated_token.get(
                api_settings.REVOKE_TOKEN_CLAIM
            )
            if (password_hash or (
                user.organization_id == 303 and not user.is_superuser
            )) and password_hash != get_md5_hash_password(user.password):
                raise AuthenticationFailed(
                    _("The user's password has been changed."), code="password_changed"
                )

        return user
