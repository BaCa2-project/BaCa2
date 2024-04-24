STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.parent / 'static'  # noqa: F821
MEDIA_ROOT = BASE_DIR.parent / 'media'  # noqa: F821
MEDIA_URL = '/data/'
MEDIA_OFFLINE_SERVING = False

ASSETS_ROOT = BASE_DIR / 'assets'  # noqa: F821

STATICFILES_DIRS = (
    ASSETS_ROOT / 'static',
)
for d in STATICFILES_DIRS:
    _auto_create_dirs.assert_exists_dir(d)  # noqa: F821
