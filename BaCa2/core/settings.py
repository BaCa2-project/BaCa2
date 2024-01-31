"""
Django settings for core project.
"""

import os

import yaml
from contextvars import ContextVar
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

from core.db.setup import DEFAULT_DB_SETTINGS
import baca2PackageManager as pkg

load_dotenv()

# dirs to be auto-created if not exist
_auto_create_dirs = []

# BASE PATH DEFINITIONS -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = BASE_DIR / 'packages_source'
SUBMITS_DIR = BASE_DIR / 'submits'
DB_BACKUP_DIR = BASE_DIR / 'backup'

_auto_create_dirs.append(PACKAGES_DIR)
_auto_create_dirs.append(SUBMITS_DIR)
_auto_create_dirs.append(DB_BACKUP_DIR)

# MAIN SECURITY SETTINGS -------------------------------------------------------------
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG')

ALLOWED_HOSTS = [
    '0.0.0.0',
    '127.0.0.1',
    'localhost',
    os.getenv('HOST_IP'),
    os.getenv('HOST_NAME')
]

# mark signal redirected via proxy as https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    'https://baca2.ii.uj.edu.pl',
    'https://127.0.0.1'
]

# APPLICATIONS -----------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'mozilla_django_oidc',  # login uj required
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'django_extensions',  # https://github.com/django-extensions/django-extensions
    'dbbackup',  # https://github.com/jazzband/django-dbbackup

    'widget_tweaks',  # https://github.com/jazzband/django-widget-tweaks

    # LOCAL APPS
    'broker_api.apps.BrokerApiConfig',
    'main',
    'course',
    'package',
    'util',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [Path.joinpath(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# MODULES LOCATION DEFINITIONS -------------------------------------------------------
ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'


# LOCALIZATION SETTINGS ---------------------------------------------------------------
LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

# DATABASES SETTINGS ------------------------------------------------------------------
DATABASES = {
    'default': DEFAULT_DB_SETTINGS | {'NAME': 'baca2db'}
}
if (SETTINGS_DIR / 'db/ext_databases.py').exists():
    exec(open((SETTINGS_DIR / 'db/ext_databases.py'), "rb").read())

# DB routing for courses
DATABASE_ROUTERS = ['course.routing.ContextCourseRouter']
currentDB = ContextVar('currentDB')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Backup settings
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': DB_BACKUP_DIR
}

# AUTHENTICATION SETTINGS ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    # Login UJ
    # 'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    # Custom authentication backend
    'BaCa2.auth_backend.BaCa2AuthBackend'
]

AUTH_USER_MODEL = 'main.User'
SITE_ID = 1

# STATIC FILES SETTINGS ---------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = "/home/zyndram/core/static/"
STATICFILES_DIRS = (
    Path.joinpath(BASE_DIR, 'assets'),
)

# LOGIN SETTINGS ---------------------------------------------------------------------
LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/main/dashboard'

# Login UJ
# OIDC_RP_CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID')
# OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET')
#
# OIDC_OP_AUTHORIZATION_ENDPOINT = 'https://auth.dev.uj.edu.pl/auth/realms/uj/.well-known/openid-configuration'
# OIDC_OP_TOKEN_ENDPOINT = 'https://auth.dev.uj.edu.pl/auth/realms/uj/.well-known/openid-configuration'
# OIDC_OP_USER_ENDPOINT = 'https://auth.dev.uj.edu.pl/auth/realms/uj/.well-known/openid-configuration'

LOGOUT_REDIRECT_URL = '/login'

##################
# APPS SETTINGS  #
##################

# import applications configuration
for f in (SETTINGS_DIR / 'app_configurations').glob('[!_]*.py'):
    exec(open(f, "rb").read())

# PACKAGE MANAGER SETTINGS -----------------------------------------------------------
pkg.set_base_dir(PACKAGES_DIR)
pkg.add_supported_extensions('cpp')

PACKAGES: Dict[str, pkg.Package] = {}

# KOLEJKA BROKER SETTINGS ------------------------------------------------------------
BROKER_URL = os.getenv('BROKER_URL')
BROKER_TIMEOUT = 600  # seconds

SUBMITS_DIR = BASE_DIR / 'submits'

# Passwords for protecting communication channels between the broker and BaCa2.
# PASSWORDS HAVE TO DIFFERENT IN ORDER TO BE EFFECTIVE
BACA_PASSWORD = 'tmp-baca-password'
BROKER_PASSWORD = 'tmp-broker-password'


class BrokerRetryPolicy:
    """Broker retry policy settings"""
    # (In seconds) specify how many retries and how often should an
    # HTTP post request be sent to the broker for one submit
    individual_submit_retry_interval = 0.05
    individual_max_retries = 5

    # (In seconds) how long it should take for a submit to become expired
    expiration_timeout = 180.0
    # (In seconds) how many times a submit should be resent after it expires
    resend_max_retries = 2
    # (In minutes) how often should expiration check be performed
    retry_check_interval = 60.0

    # (In minutes) specify how old should error submits be before they are deleted
    deletion_timeout = 60.0 * 24
    # (In minutes) specify how often should the deletion check be performed
    deletion_check_interval = 60.0 * 6

    # Auto start broker daemons
    auto_start = True


# import secrets
SECRETS_DIR = BASE_DIR / "secrets.yaml"
SECRETS = {}
if SECRETS_DIR.exists() and SECRETS_DIR.is_file():
    with open(SECRETS_DIR) as secrets_file:
        SECRETS = yaml.safe_load(secrets_file)

# USOS SETTINGS ---------------------------------------------------------------------
USOS_CONSUMER_KEY = os.getenv('USOS_CONSUMER_KEY')
USOS_CONSUMER_SECRET = os.getenv('USOS_CONSUMER_SECRET')
USOS_GATEWAY = os.getenv('USOS_GATEWAY')
USOS_SCOPES = [
    'offline_access',
    'crstests',
    'email',
    'grades',
    'grades_write',
    'mailclient',
    'other_emails',
    'staff_perspective',
]

# AUTO-CREATE SELECTED DIRS -----------------------------------------------------------
for d in _auto_create_dirs:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)


# LOGGING SETTINGS --------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': [],
        }
    },
    'loggers': {
        loger_name: {
            'level': 'INFO',
            'propagate': True,
        } for loger_name in ('broker_api', 'course', 'package', 'util', 'main', 'django')
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
}
