from django.core.cache import cache

REPORTER_PROXY_ACCESS_TOKEN_KEY = "reporter_proxy_access_token"
REPORTER_PROXY_REFRESH_TOKEN_KEY = "reporter_proxy_refresh_token"


def set_token(access_token, refresh_token=""):
    cache.set(REPORTER_PROXY_ACCESS_TOKEN_KEY, access_token)
    if refresh_token:
        cache.set(REPORTER_PROXY_REFRESH_TOKEN_KEY, refresh_token)


def get_access_token():
    return cache.get(REPORTER_PROXY_ACCESS_TOKEN_KEY)


def get_refresh_token():
    return cache.get(REPORTER_PROXY_REFRESH_TOKEN_KEY)
