import os

from pathlib import Path
from split_settings.tools import include, optional
from dotenv import load_dotenv

from core.tools.path_creator import PathCreator

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

include(
    'security.py',
    'apps.py',
    'base.py',
    'localization.py',
    'database.py',
    'authentication.py',
    'static_files.py',
    'login.py',
    'packages.py',
    'broker.py',
    'usos.py',
    'logging.py',
    optional(str(LOCAL_SETTINGS_PATH)),
    'envvars.py',
)

_auto_create_dirs.create()
