"""
Django settings for BaCa2 project.
"""

import os

import yaml
from contextvars import ContextVar
from pathlib import Path
from typing import Dict

from colorlog import ColoredFormatter
from dotenv import load_dotenv

from BaCa2.db.setup import DEFAULT_DB_SETTINGS
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
ROOT_URLCONF = 'BaCa2.urls'
WSGI_APPLICATION = 'BaCa2.wsgi.application'

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
STATIC_ROOT = "/home/zyndram/BaCa2/static/"
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


import logging
import pathlib


class CustomFormatter(logging.Formatter):
    """
    Custom formatter for BaCa2 logs. Adds levelname, pathname, and funcName formatting.
    """

    def __init__(self,
                 fmt: str,
                 const_levelname_width: bool = True,
                 levelname_width: int = 10,
                 dot_pathname: bool = True,
                 **kwargs) -> None:
        """
        :param fmt: format string
        :type fmt: str
        :param const_levelname_width: whether to use constant levelname width
        :type const_levelname_width: bool
        :param levelname_width: constant levelname width, default is 10
        :type levelname_width: int
        :param dot_pathname: whether to replace path separators with dots
        :type dot_pathname: bool
        """
        if not hasattr(self, 'funcName_after_pathname'):
            self.funcName_after_pathname = self.funcname_after_pathname(fmt)

        fmt = self.format_lineno(fmt)

        self.const_levelname_width = const_levelname_width
        self.levelname_width = levelname_width
        self.dot_pathname = dot_pathname

        super().__init__(fmt=fmt, style='%', **kwargs)

    @staticmethod
    def funcname_after_pathname(fmt: str) -> bool:
        """
        :param fmt: format string
        :type fmt: str
        :return: whether the funcName is placed after the pathname in the format string
        :rtype: bool
        """
        if '%(pathname)s' in fmt and '%(funcName)s' in fmt:
            p_index = fmt.find('%(pathname)s')
            f_index = p_index + len('%(pathname)s')
            return fmt.startswith('%(funcName)s', f_index)
        else:
            return False

    def format_lineno(self, fmt: str) -> str:
        """
        :param fmt: format string
        :type fmt: str
        :return: format string with modified lineno format
        :rtype: str
        """
        return fmt.replace('%(lineno)d', f'%(lineno)d::')

    def format(self, record) -> str:
        """
        Format the levelname, pathname, and funcName in the log record. Restore the original
        values after generating the log message.

        :param record: log record
        :type record: logging.LogRecord
        :return: formatted log message
        :rtype: str
        """
        levelname = record.levelname
        pathname = record.pathname
        funcname = record.funcName
        self.format_levelname(record)
        self.format_pathname(record)
        self.format_funcname(record)
        out = super().format(record)
        record.levelname = levelname
        record.pathname = pathname
        record.funcName = funcname
        return out

    def format_funcname(self, record) -> None:
        """
        Formats the funcName in the log record.

        :param record: log record
        :type record: logging.LogRecord
        """
        record.funcName = f'{record.funcName}:'

    def format_pathname(self, record) -> None:
        """
        Formats the pathname in the log record. Relativaize the pathname to the BASE_DIR or the
        django directory, and replace path separators with dots if dot_pathname is True.

        :param record: log record
        :type record: logging.LogRecord
        """
        from django.conf import settings

        pathname = pathlib.Path(record.pathname)

        if 'django' in pathname.parts:
            pathname = pathname.relative_to(pathname.parents[~(pathname.parts.index('django') - 1)])
        else:
            pathname = pathname.relative_to(settings.BASE_DIR)

        pathname = str(pathname.with_suffix(''))

        if self.dot_pathname:
            pathname = self.format_dot_pathname(pathname)

        record.pathname = pathname

    def format_dot_pathname(self, pathname: str) -> str:
        """
        :param pathname: pathname
        :type pathname: str
        :return: pathname with path separators replaced by dots
        :rtype: str
        """
        pathname = pathname.replace('\\', '.').replace('/', '.')

        if self.funcName_after_pathname:
            pathname = f'{pathname}.'

        return pathname

    def format_levelname(self, record) -> None:
        """
        Formats the levelname in the log record. Adds square brackets around the levelname and
        pads it to the levelname_width if const_levelname_width is True.

        :param record: log record
        :type record: logging.LogRecord
        """
        record.levelname = f'[{record.levelname}]'

        if self.const_levelname_width:
            record.levelname = record.levelname.ljust(self.levelname_width)


class CustomColoredFormatter(CustomFormatter):
    """
    Custom formatter for BaCa2 logs. Adds levelname and pathname formatting and allows for fully
    customizable log coloring.
    """

    #: names of all allowed record attributes
    RECORD_ATTRS = ('%(name)s', '%(levelno)s', '%(levelname)s', '%(pathname)s', '%(filename)s',
                    '%(module)s', '%(lineno)d', '%(funcName)s', '%(created)f', '%(asctime)s',
                    '%(msecs)d', '%(relativeCreated)d', '%(thread)d', '%(threadName)s',
                    '%(process)d', '%(message)s')

    #: default colors for log elements. Can be overridden by passing a custom colors_dict to the
    #: formatter constructor. The keys are the names of the record attributes and levels, as well as
    #: 'BRACES' for the square brackets around the levelname, 'DEFAULT' for the default color to use
    #: on elements that do not have specific color assigned, 'RESET' for the reset color code, and
    #: 'SPECIAL' used for special characters when formatting the log message.
    COLORS = {
        'DEFAULT': '\033[97m',  # White
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',  # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[101m\033[30m',  # White text on red background
        'BRACES': '\033[37m',  # Gray
        'RESET': '\033[0m',  # Reset
        'SPECIAL': '\033[95m',  # Purple
        '%(asctime)s': '\033[32m',  # Green
        '%(pathname)s': '\033[37m',  # Gray
        '%(funcName)s': '\033[37m',  # Gray
        '%(lineno)d': '\033[36m',  # Cyan
        '%(name)s': '\033[37m',  # Gray
    }

    def __init__(self,
                 fmt: str,
                 colors_dict: Dict[str, str] = None,
                 const_levelname_width: bool = True,
                 levelname_width: int = 10,
                 dot_pathname: bool = True,
                 **kwargs) -> None:
        """
        :param fmt: format string
        :type fmt: str
        :param colors_dict: custom colors for log elements
        :type colors_dict: dict
        :param const_levelname_width: whether to use constant levelname width
        :type const_levelname_width: bool
        :param levelname_width: constant levelname width, default is 10
        :type levelname_width: int
        :param dot_pathname: whether to replace path separators with dots
        :type dot_pathname: bool
        """
        self.funcName_after_pathname = self.funcname_after_pathname(fmt)
        self.colors_dict = CustomColoredFormatter.COLORS

        if colors_dict:
            self.colors_dict.update(colors_dict)

        fmt = self.add_colors(fmt)

        super().__init__(fmt=fmt,
                         const_levelname_width=const_levelname_width,
                         levelname_width=levelname_width,
                         dot_pathname=dot_pathname, **kwargs)

    def add_colors(self, fmt: str) -> str:
        """
        Add colors to the log elements in the format string according to the colors_dict.

        :param fmt: format string
        :type fmt: str
        :return: format string with colors
        :rtype: str
        """
        reset = self.colors_dict.get('RESET', '')
        default = self.colors_dict.get('DEFAULT', reset)

        for attr in CustomColoredFormatter.RECORD_ATTRS:
            if attr in fmt:
                color = self.colors_dict.get(attr, default)
                fmt = fmt.replace(attr, f'{color}{attr}{reset}')

        return fmt

    def special_symbol(self, symbol: str, following_element: str = '') -> str:
        """
        Add color to a special symbol used in the log message formatting.

        :param symbol: special symbol
        :type symbol: str
        :param following_element: log message element following the special symbol
        (e.g. '%(message)s'), its color will be added following the special symbol (optional)
        :type following_element: str
        :return: special symbol with color
        :rtype: str
        """
        reset = self.colors_dict.get('RESET', '')
        default = self.colors_dict.get('DEFAULT', reset)
        special_color = self.colors_dict.get('SPECIAL', default)
        symbol = f'{special_color}{symbol}{reset}'

        if following_element:
            following_color = self.colors_dict.get(following_element, default)
            return f'{symbol}{following_color}'

        return symbol

    def format_lineno(self, fmt: str) -> str:
        """
        :param fmt: format string
        :type fmt: str
        :return: format string with modified lineno format
        :rtype: str
        """
        return fmt.replace('%(lineno)d', f'%(lineno)d{self.special_symbol("::")}')

    def format_funcname(self, record) -> None:
        """
        Formats the funcName in the log record.

        :param record: log record
        :type record: logging.LogRecord
        """
        record.funcName = f'{record.funcName}{self.special_symbol(":")}'

    def format_dot_pathname(self, pathname: str) -> str:
        """
        :param pathname: pathname
        :type pathname: str
        :return: pathname with path separators replaced by dots
        :rtype: str
        """
        dot = self.special_symbol('.', '%(pathname)s')
        pathname = pathname.replace('\\', dot).replace('/', dot)

        if self.funcName_after_pathname:
            dot = self.special_symbol('.')
            pathname = f'{pathname}{dot}'

        return pathname

    def format_levelname(self, record) -> None:
        """
        Formats the levelname in the log record. Adds square brackets around the levelname and
        pads it to the levelname_width if const_levelname_width is True.

        :param record: log record
        :type record: logging.LogRecord
        """
        added_width = 0
        r = self.colors_dict.get('RESET', '')
        color = self.colors_dict.get(record.levelname, r)
        braces_color = self.colors_dict.get('BRACES', '')
        added_width += len(color) + len(r) * 3 + len(braces_color) * 2
        record.levelname = f'{braces_color}[{r}{color}{record.levelname}{r}{braces_color}]{r}'

        if self.const_levelname_width:
            record.levelname = record.levelname.ljust(self.levelname_width + added_width)


LOGS_DIR = BASE_DIR / 'logs'

FORMATTERS = {
    'simple': {
        '()': 'BaCa2.settings.CustomColoredFormatter',
        'fmt': '%(levelname)s '
               '%(asctime)s '
               '%(pathname)s'
               '%(funcName)s'
               '%(lineno)d '
               '%(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'server_console': {
        '()': 'BaCa2.settings.CustomColoredFormatter',
        'fmt': '%(levelname)s '
               '%(asctime)s '
               '%(name)s\033[95m::\033[0m '
               '%(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'verbose': {
        '()': 'BaCa2.settings.CustomFormatter',
        'fmt': '%(levelname)s '
               '%(asctime)s '
               '%(threadName)s '
               '%(thread)d '
               '%(process)d '
               '%(pathname)s'
               '%(funcName)s'
               '%(lineno)d '
               '%(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
}

HANDLERS = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'simple',
        'level': 'DEBUG',
    },
    'server_console': {
        'class': 'logging.StreamHandler',
        'formatter': 'server_console',
        'level': 'DEBUG',
    },
    'info': {
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'verbose',
        'level': 'INFO',
        'filename': str(LOGS_DIR / 'info.log'),
        'mode': 'a',
        'encoding': 'utf-8',
        'backupCount': 5,
        'maxBytes': 1024 * 1024,
    },
    'error': {
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'verbose',
        'level': 'ERROR',
        'filename': str(LOGS_DIR / 'error.log'),
        'mode': 'a',
        'encoding': 'utf-8',
        'backupCount': 5,
        'maxBytes': 1024 * 1024,
    },
}

LOGGERS = {
    'django': {
      'handlers': ['console', 'info'],
      'level': 'INFO',
    },
    'django.request': {
      'handlers': ['error'],
      'level': 'INFO',
      'propagate': True,
    },
    'django.server': {
      'handlers': ['error', 'server_console'],
      'level': 'INFO',
      'propagate': False,
    },
    'django.template': {
      'handlers': ['error'],
      'level': 'DEBUG',
      'propagate': False,
    },
} | {
    app_name: {
      'handlers': ['console', 'info', 'error'],
      'level': 'DEBUG',
    } for app_name in ('broker_api', 'course', 'package', 'util', 'main')
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': FORMATTERS,
    'handlers': HANDLERS,
    'loggers': LOGGERS,
}
