# pylint: disable=unused-wildcard-import, wildcard-import
from .settings import *

# Sentry
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

DEBUG = False

# AWS S3 SETTINGS
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_MEDIA_BUCKET_NAME = os.environ['AWS_MEDIA_BUCKET_NAME']
STATICFILES_STORAGE = 'common.buckets.CachedS3Boto3Storage'
DEFAULT_FILE_STORAGE = 'common.buckets.S3MediaStorage'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-southeast-1')
AWS_S3_CUSTOM_DOMAIN = 'cdn.mydomain.com'
AWS_QUERYSTRING_AUTH = False
AWS_PRELOAD_METADATA = True
AWS_DEFAULT_ACL = None
AWS_IS_GZIPPED = True

STATIC_URL = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
# For fixing additional slash in s3
_STATIC_URL = STATIC_URL
FULL_STATIC_URL = f"https://{STATIC_URL}"
MEDIA_URL = f"{AWS_MEDIA_BUCKET_NAME}.s3.amazonaws.com/"
# For fixing additional slash in s3
_MEDIA_URL = MEDIA_URL
FULL_MEDIA_URL = f"https://{MEDIA_URL}"

COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_URL = f"https://{STATIC_URL}"


ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

ADMINS = (
    ('Faisal Mahmud', 'faisal@healthos.io'),
    ('Ashraful Alam', 'ashraful@healthos.io'),
)

DATABASES = {
    'default': dj_database_url.config(env='DATABASE_URL'),
    'replica_01': dj_database_url.config(env='REPLICA_01_DATABASE_URL'),
    'replica_02': dj_database_url.config(env='REPLICA_02_DATABASE_URL'),
    'no-pooling': dj_database_url.config(env='DATABASE_URL')
}

DATABASE_ROUTERS = ['projectile.dbrouters.DatabaseRouter',]

# SECURITY WARNING: keep the secret key used in production secret!
# The SECRET_KEY value should be set in /etc/environment
# Use the management command 'common_secret_key' in order to create a new one
SECRET_KEY = os.environ['SECRET_KEY']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'elasticapm': {
            'level': 'WARNING',
            'class': 'elasticapm.contrib.django.handlers.LoggingHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'core': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'common': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        # Log errors from the Elastic APM module to the console (recommended)
        'elasticapm.errors': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

# EMAIL SETTINGS
# EMAIL_USE_TLS = True
# EMAIL_BACKEND = 'djrill.mail.backends.djrill.DjrillBackend'
# DEFAULT_FROM_EMAIL = 'HealthOS <mail@healthosbd.com>'
# SERVER_EMAIL = 'mail@healthosbd.com'
# EMAIL_SUBJECT_PREFIX = '[HealthOS] '

# HTTPS SETTINGS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CUSTOM DB ROUTER
MIDDLEWARE = ('projectile.dbrouters.RouterMiddleware',) + MIDDLEWARE

# ELASTIC APM
INSTALLED_APPS = ['elasticapm.contrib.django',] + INSTALLED_APPS
MIDDLEWARE = ('elasticapm.contrib.django.middleware.TracingMiddleware',) + MIDDLEWARE

ELASTIC_APM = {
    # Set required service name. Allowed characters:
    # a-z, A-Z, 0-9, -, _, and space
    'SERVICE_NAME': os.environ.get('ELASTICAPM_SERVICE_NAME', ''),
    # Use if APM Server requires a token
    'SECRET_TOKEN': os.environ.get('ELASTICAPM_SECRET_TOKEN', ''),
    # Set custom APM Server URL (default: http://localhost:8200)
    'SERVER_URL': os.environ.get('ELASTICAPM_SERVER_URL', ''),
}

# Elastic Search related configuartion
ES_INDEX = 'omis'

ELASTICSEARCH_DSL = {
    'default': {'hosts': os.environ.get('ES_SERVER_IP')},
}

ES_PAGINATION_SIZE = 100
ES_MAX_PAGINATION_SIZE = 1000


# REST FRAMEWORK
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
})

# INFOBIP SMS GATEWAY SETTINGS
INFOBIP_API_KEY = os.environ.get('INFOBIP_API_KEY', '')

# SENTRY SETTINGS
sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'],
    integrations=[DjangoIntegration(), RedisIntegration(), CeleryIntegration()],
    traces_sample_rate=0.3,
    profiles_sample_rate=0.3,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)
