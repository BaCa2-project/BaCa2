"""
Django settings for BaCa2 project.

Generated by 'django-admin startproject' using Django 4.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import yaml
from contextvars import ContextVar
from pathlib import Path
from typing import Dict

from BaCa2.db.setup import DEFAULT_DB_SETTINGS
import baca2PackageManager as pkg

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = BASE_DIR / 'packages_source'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-h)q%%z-63-!_w*7qsme!7j#1n6_9_v6r+4e%k1u+va@dz4p%x#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'broker_api.apps.BrokerApiConfig',

    'allauth',  # https://github.com/pennersr/django-allauth
    'allauth.account',
    'allauth.socialaccount',

    'django_extensions',  # https://github.com/django-extensions/django-extensions
    'dbbackup',  # https://github.com/jazzband/django-dbbackup

    'widget_tweaks',  # https://github.com/jazzband/django-widget-tweaks

    'main',  # local app

    'course',  # local app

    'package',  # local app

    'util',  # local app
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

ROOT_URLCONF = 'BaCa2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [Path.joinpath(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'BaCa2.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'pl'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases


DATABASES = {
    'default': DEFAULT_DB_SETTINGS | {'NAME': 'baca2db'}
}
if (SETTINGS_DIR / 'db/ext_databases.py').exists():
    exec(open((SETTINGS_DIR / 'db/ext_databases.py'), "rb").read())

# DB routing
# https://docs.djangoproject.com/en/4.1/topics/db/multi-db/
DATABASE_ROUTERS = ['course.routing.ContextCourseRouter']

currentDB = ContextVar('currentDB')

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
    # Custom authentication backend
    'BaCa2.auth_backend.BaCa2AuthBackend'

    # Needed to login by username in Django admin, regardless of `allauth`
    # 'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    # 'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_USER_MODEL = 'main.User'

SITE_ID = 1  # allauth required

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/main/dashboard'

STATICFILES_DIRS = (
    Path.joinpath(BASE_DIR, 'assets'),
)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

##################
# APPS SETTINGS  #
##################

# import applications configuration
for f in (SETTINGS_DIR / 'app_configurations').glob('[!_]*.py'):
    exec(open(f, "rb").read())

if (SETTINGS_DIR / "settings_local.py").exists():
    exec(open(SETTINGS_DIR / "settings_local.py", "rb").read())

if not PACKAGES_DIR.is_dir():
    PACKAGES_DIR.mkdir()

pkg.set_base_dir(PACKAGES_DIR)
pkg.add_supported_extensions('cpp')

PACKAGES: Dict[str, pkg.Package] = {}

BROKER_URL = 'http://127.0.0.1:8180/baca/'
BROKER_TIMEOUT = 600  # seconds

SUBMITS_DIR = BASE_DIR / 'submits'

# Passwords for protecting communication channels between the broker and BaCa2.
# PASSWORDS HAVE TO DIFFERENT IN ORDER TO BE EFFECTIVE
BACA_PASSWORD = 'tmp-baca-password'
BROKER_PASSWORD = 'tmp-broker-password'

# import secrets
SECRETS_DIR = BASE_DIR / "secrets.yaml"
SECRETS = {}
if SECRETS_DIR.exists() and SECRETS_DIR.is_file():
    with open(SECRETS_DIR) as secrets_file:
        SECRETS = yaml.safe_load(secrets_file)

