from contextvars import ContextVar

from core.db.setup import DEFAULT_DB_SETTINGS

DB_BACKUP_DIR = BASE_DIR / 'backup'  # noqa: F821
_auto_create_dirs.add_dir(DB_BACKUP_DIR)  # noqa: F821
DB_SETTINGS_DIR = BASE_DIR / 'core' / 'db'  # noqa: F821
_auto_create_dirs.assert_exists_dir(DB_SETTINGS_DIR, instant=True)  # noqa: F821

DATABASES = {
    'default': DEFAULT_DB_SETTINGS | {'NAME': 'baca2db'}
}
if (DB_SETTINGS_DIR / 'ext_databases.py').exists():
    exec(open((DB_SETTINGS_DIR / 'ext_databases.py'), 'rb').read())

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
