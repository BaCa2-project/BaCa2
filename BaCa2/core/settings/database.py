import os
from contextvars import ContextVar

from core.db.manager import DBManager

DB_BACKUP_DIR = BASE_DIR / 'backup'  # noqa: F821
_auto_create_dirs.add_dir(DB_BACKUP_DIR)  # noqa: F821
DB_SETTINGS_DIR = BASE_DIR / 'core' / 'db'  # noqa: F821
_auto_create_dirs.assert_exists_dir(DB_SETTINGS_DIR, instant=True)  # noqa: F821
DB_DEFINITIONS_FILE = DB_SETTINGS_DIR / 'db.cache'
_auto_create_dirs.add_file(DB_DEFINITIONS_FILE)  # noqa: F821

BACA2_DB_USER = os.getenv('BACA2_DB_USER', 'baca2')
BACA2_DB_PASSWORD = os.getenv('BACA2_DB_PASSWORD')
BACA2_DB_ROOT_USER = os.getenv('BACA2_DB_ROOT_USER', 'root')
BACA2_DB_ROOT_PASSWORD = os.getenv('BACA2_DB_ROOT_PASSWORD')
DEFAULT_DB_KEY = 'baca2db'
DEFAULT_DB_HOST = 'localhost'

DEFAULT_DB_SETTINGS = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'USER': BACA2_DB_USER,
    'PASSWORD': BACA2_DB_PASSWORD,
    'HOST': 'localhost',
    'PORT': '',
    'TIME_ZONE': None,
    'CONN_HEALTH_CHECKS': False,
    'CONN_MAX_AGE': 0,
    'AUTOCOMMIT': True,
    'OPTIONS': {},
    'ATOMIC_REQUESTS': False
}

DATABASES = {}

DB_MANAGER = DBManager(
    cache_file=DB_DEFINITIONS_FILE,
    default_settings=DEFAULT_DB_SETTINGS,
    root_user=BACA2_DB_ROOT_USER,
    root_password=BACA2_DB_ROOT_PASSWORD,
    db_host=DEFAULT_DB_HOST,
    databases=DATABASES,
    default_db_key=DEFAULT_DB_KEY,
)
DB_MANAGER.parse_cache()

# DB routing for courses
DATABASE_ROUTERS = ['course.routing.ContextCourseRouter']
CURRENT_DB = ContextVar('CURRENT_DB')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Backup settings
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': DB_BACKUP_DIR
}
