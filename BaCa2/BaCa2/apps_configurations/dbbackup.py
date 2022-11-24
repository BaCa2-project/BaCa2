from pathlib import Path

BACKUP_DIR = Path(__file__).resolve().parent.parent.parent
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': BACKUP_DIR / 'backup'
}