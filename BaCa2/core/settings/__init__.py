import os
from pathlib import Path

from core.tools.path_creator import PathCreator
from dotenv import load_dotenv
from split_settings.tools import include, optional

load_dotenv()

# dirs to be auto-created if not exist
_auto_create_dirs = PathCreator()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = BASE_DIR.absolute()

ENVVAR_SETTINGS_PREFIX = 'BACA2_WEB_'

LOCAL_SETTINGS_PATH = os.getenv(f'{ENVVAR_SETTINGS_PREFIX}LOCAL_SETTINGS_PATH')
if not LOCAL_SETTINGS_PATH:
    LOCAL_SETTINGS_PATH = BASE_DIR / 'local' / 'settings.dev.py'

LOCAL_SETTINGS_PATH = LOCAL_SETTINGS_PATH.absolute()

OS_NAME = 'unknown'
if os.name == 'nt':
    OS_NAME = 'windows'
elif os.name == 'posix':
    OS_NAME = 'unix'

include(
    'security.py',
    'apps.py',
    'base.py',
    'localization.py',
    'logs.py',
    'database.py',
    'authentication.py',
    'login.py',
    'packages.py',
    'broker.py',
    'static_files.py',
    'usos.py',
    'email.py',
    optional(str(LOCAL_SETTINGS_PATH)),
    'envvars.py',
)

_auto_create_dirs.create()
