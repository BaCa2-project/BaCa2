STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.parent / 'static'  # noqa: F821
# MEDIA_ROOT = BASE_DIR.parent / 'media'  # noqa: F821
# MEDIA_URL = '/data/'

ASSETS_ROOT = BASE_DIR / 'assets'  # noqa: F821

STATICFILES_DIRS = (
    ASSETS_ROOT / 'static',
    TASK_DESCRIPTIONS_DIR,  # noqa: F821
    SUBMITS_DIR,  # noqa: F821
    ATTACHMENTS_DIR,  # noqa: F821
    BASE_DIR.parent / 'node_modules',  # noqa: F821
)
for d in STATICFILES_DIRS:
    _auto_create_dirs.assert_exists_dir(d)  # noqa: F821
