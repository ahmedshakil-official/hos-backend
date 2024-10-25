import os
from django.conf import settings

from rest_framework.settings import APISettings

from reporter_proxy.helpers import get_access_token

DEFAULTS = {
    "HOST": None,
    "AUTH": {
        "user": None,
        "password": None,
        "token": None,
    },
    "TIMEOUT": None,
    "DEFAULT_HTTP_ACCEPT": "application/json",
    "DEFAULT_HTTP_ACCEPT_LANGUAGE": "en-US,en;q=0.8",
    "DEFAULT_CONTENT_TYPE": "application/json",
    # Return response as-is if enabled
    "RETURN_RAW": False,
    # Return failure response as-is if code >= 400
    "RETURN_RAW_ERROR": False,
    # Used to translate Accept HTTP field
    "ACCEPT_MAPS": {
        "text/html": "application/json",
    },
    # Do not pass following parameters
    "DISALLOWED_PARAMS": ("format",),
    # Perform a SSL Cert Verification on URI requests are being proxied to
    "VERIFY_SSL": True,
}


PROXY_CONFIG = {
    "HOST": os.environ.get("REPORTER_BASE_URL", "http://localhost:8000"),
    "AUTH": {
        # 'user': 'myuser',
        # 'password': 'mypassword',
        # Or using token:
        "token": f"Bearer {get_access_token()}",
    },
    "RETURN_RAW_ERROR": True,
}

api_proxy_configs = APISettings(PROXY_CONFIG, DEFAULTS)
