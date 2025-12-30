import os
from datetime import timedelta

import django
from django.utils.encoding import smart_str
from django.utils.translation import gettext, gettext_lazy
from environ import Env
from raven import fetch_git_sha
from raven.exceptions import InvalidGitRepository

# Prevent warning regarding
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

django.utils.translation.ugettext_lazy = gettext_lazy
django.utils.translation.ugettext = gettext
django.utils.encoding.smart_text = smart_str


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert os.path.isfile(os.path.join(BASE_DIR, 'manage.py'))

#####################
# Local environment #
#####################
env = Env(
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    # Authentication settings
    OIDC_API_AUDIENCE=(list, []),
    OIDC_API_SCOPE_PREFIX=(str, ''),
    OIDC_API_REQUIRE_SCOPE_FOR_AUTHENTICATION=(bool, True),
    OIDC_API_ISSUER=(str, ''),
    OIDC_API_AUTHORIZATION_FIELD=(str, ''),
    SOCIAL_AUTH_TUNNISTAMO_KEY=(str, ''),
    SOCIAL_AUTH_TUNNISTAMO_SECRET=(str, ''),
    SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT=(str, ''),
)
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    env.read_env(env_file)

########################
# Django core settings #
########################
DEBUG = env.bool('DEBUG', default=False)
TIER = env.str('TIER', default='dev')
SECRET_KEY = env.str('SECRET_KEY', default=('' if not DEBUG else 'xxx'))
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
USE_X_FORWARDED_HOST = True

#########
# Paths #
#########
MEDIA_ROOT = env("MEDIA_ROOT", default='')
MEDIA_URL = '/media/'
ROOT_URLCONF = 'parkkihubi.urls'
STATIC_ROOT = env("STATIC_ROOT", default='')
STATIC_URL = '/static/'

############
# Database #
############
DATABASES = {
    'default': env.db_url(default='postgis:///parkkihubi'),
}

TEST_DATABASE_TEMPLATE = env.str("TEST_DATABASE_TEMPLATE", default="")
if TEST_DATABASE_TEMPLATE:
    DATABASES['default']['TEST'] = {'TEMPLATE': TEST_DATABASE_TEMPLATE}

##########
# Caches #
##########
CACHES = {'default': env.cache_url(default='locmemcache://')}

##################
# Installed apps #
##################
INSTALLED_APPS = [
    'helusers.apps.HelusersConfig',  # Helusers app (provides models)
    # Note: helusers.providers.helsinki_oidc is not required - Tunnistamo works for any city
    'social_django',  # Required for OAuth/OIDC authentication
    'helusers.apps.HelusersAdminConfig',  # Replaces django.contrib.admin with Tunnistamo support
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'raven.contrib.django.raven_compat',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_gis',
    'django_filters',
    'parkkihubi',
    'parkings',
    'sanitized_dump',
] + env.list("EXTRA_INSTALLED_APPS", default=['parkkihubi_hel'])


if DEBUG and TIER == 'dev':
    # shell_plus and other goodies
    INSTALLED_APPS.append("django_extensions")

##############
# Middleware #
##############
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'parkkihubi.middleware.MethodOverrideMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'parkkihubi.middleware.AdminTimezoneMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

#######################
# Authentication      #
#######################
AUTHENTICATION_BACKENDS = (
    'helusers.tunnistamo_oidc.TunnistamoOIDCAuth',
    'django.contrib.auth.backends.ModelBackend',  # Keep for password login fallback
)

# Session serializer required for helusers (stores datetime objects)
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Session cookie settings for cross-origin requests (Dashboard on different port/domain)
# For localhost development with different ports, SameSite=Lax should work
# For production with different domains, may need SameSite=None and Secure=True
SESSION_COOKIE_SAMESITE = 'Lax'  # 'Lax' works for localhost:3000 -> localhost:8000
SESSION_COOKIE_HTTPONLY = True  # Security: prevent JavaScript access to session cookie
# SESSION_COOKIE_SECURE = True  # Set to True in production (HTTPS only)

# Helusers OIDC API Token Auth settings (required by helusers)
OIDC_API_TOKEN_AUTH = {
    'AUDIENCE': env('OIDC_API_AUDIENCE'),
    'API_SCOPE_PREFIX': env('OIDC_API_SCOPE_PREFIX'),
    'API_AUTHORIZATION_FIELD': env('OIDC_API_AUTHORIZATION_FIELD'),
    'REQUIRE_API_SCOPE_FOR_AUTHENTICATION': env('OIDC_API_REQUIRE_SCOPE_FOR_AUTHENTICATION'),
    'ISSUER': env('OIDC_API_ISSUER'),
}

# Logout redirect URL (required by helusers for social auth logout)
LOGOUT_REDIRECT_URL = '/admin/'

# Default login redirect URL (Django default is /accounts/profile/)
# We use a custom redirect view to handle 'next' parameter properly
LOGIN_REDIRECT_URL = '/login-redirect/'

# Social auth (Tunnistamo) redirect settings
# After successful login, redirect to our custom redirect view which handles 'next' parameter
# social_django will automatically append ?next=... to the redirect URL if it was passed
# in the OAuth authorization URL (which we do in the template)
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/login-redirect/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/login-redirect/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/admin/login/'

# Social auth provider configuration for Tunnistamo
# The provider name 'tunnistamo' is used by helusers
SOCIAL_AUTH_TUNNISTAMO_KEY = env('SOCIAL_AUTH_TUNNISTAMO_KEY')
SOCIAL_AUTH_TUNNISTAMO_SECRET = env('SOCIAL_AUTH_TUNNISTAMO_SECRET')
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = env('SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT')

#############
# Templates #
#############
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

##########
# Sentry #
##########
try:
    git_sha = fetch_git_sha(BASE_DIR)
except InvalidGitRepository:
    git_sha = None
RAVEN_CONFIG = {
    'dsn': env.str('SENTRY_DSN', default=None),
    'release': git_sha,
}

############################
# Languages & Localization #
############################
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
ADMIN_TIME_ZONE = 'Europe/Helsinki'
USE_I18N = True
USE_TZ = True

########
# WSGI #
########
WSGI_APPLICATION = 'parkkihubi.wsgi.application'

##########
# Mailer #
##########
vars().update(env.email_url(
    default=('consolemail://' if DEBUG else 'smtp://localhost:25')
))
DEFAULT_FROM_EMAIL = 'no-reply.parkkihubi@fiupparkp01.anders.fi'

#########################
# Django REST Framework #
#########################
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        # Make nothing accessible to non-admins by default.  Viewsets
        # should specify permission_classes to override permissions.
        'rest_framework.permissions.IsAdminUser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'parkings.authentication.ApiKeyAuthentication',
        'helusers.tunnistamo_oidc.TunnistamoOIDCAuth',
        'rest_framework.authentication.SessionAuthentication',  # Required for Dashboard Tunnistamo auth
    ] + ([  # Following is only for DEBUG mode in dev environment:
        'rest_framework.authentication.BasicAuthentication',
    ] if (DEBUG and TIER == 'dev') else []),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'ALLOWED_VERSIONS': ('v1',),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'EXCEPTION_HANDLER': 'parkings.exception_handler.parkings_exception_handler',
    'PAGE_SIZE': 100,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# JWT and 2FA authentication removed - using Tunnistamo OIDC instead
# JWT_AUTH = {
#     'JWT_EXPIRATION_DELTA': timedelta(minutes=30),
#     'JWT_ALLOW_REFRESH': True,
#     'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
# }
#
# JWT2FA_AUTH = {
#     'CODE_TOKEN_THROTTLE_RATE': '5/15m',
#     'AUTH_TOKEN_RETRY_WAIT_TIME': timedelta(seconds=10),
#     'EMAIL_SENDER_SUBJECT_OVERRIDE': '{code} - Varmennuskoodisi',
#     'EMAIL_SENDER_BODY_OVERRIDE': (
#         'Hei!\n'
#         '\n'
#         'Varmennuskoodisi kirjautumista varten on: {code}\n'
#         '\n'
#         't. Parkkihubi'),
# }

# CORS settings - allow all origins and credentials for Dashboard integration
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True  # Required for session cookies to work with CORS

##############
# Parkkihubi #
##############
PARKKIHUBI_TIME_PARKINGS_EDITABLE = timedelta(minutes=2)
PARKKIHUBI_TIME_EVENT_PARKINGS_EDITABLE = timedelta(minutes=2)
PARKKIHUBI_TIME_OLD_PARKINGS_VISIBLE = timedelta(minutes=15)
PARKKIHUBI_NONE_END_TIME_REPLACEMENT = env.str(
    'PARKKIHUBI_NONE_END_TIME_REPLACEMENT', default='')
PARKKIHUBI_PUBLIC_API_ENABLED = env.bool('PARKKIHUBI_PUBLIC_API_ENABLED', True)
PARKKIHUBI_MONITORING_API_ENABLED = env.bool(
    'PARKKIHUBI_MONITORING_API_ENABLED', True)
PARKKIHUBI_OPERATOR_API_ENABLED = env.bool('PARKKIHUBI_OPERATOR_API_ENABLED', True)
PARKKIHUBI_ENFORCEMENT_API_ENABLED = (
    env.bool('PARKKIHUBI_ENFORCEMENT_API_ENABLED', True))
PARKKIHUBI_DATA_API_ENABLED = env.bool('PARKKIHUBI_DATA_API_ENABLED', True)

PARKKIHUBI_PERMITS_PRUNABLE_AFTER = timedelta(days=3)
DEFAULT_ENFORCEMENT_DOMAIN = ('Turku', 'TKU')  # Changed from ('Helsinki', 'HKI')
PARKKIHUBI_REGISTRATION_NUMBERS_REMOVABLE_AFTER = timedelta(hours=24)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)-8s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'loggers': {
        'root': {
            'handlers': ['sentry'],
            'level': 'WARNING',
        },
        'parkings': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

FILE_UPLOAD_PERMISSIONS = 0o644
