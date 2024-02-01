STATIC_URL = '/static/'
STATIC_ROOT = "/home/zyndram/core/static/"
STATICFILES_DIRS = (
    BASE_DIR / 'assets',  # type: ignore # noqa: F821
)
for d in STATICFILES_DIRS:
    _auto_create_dirs.assert_exists_dir(d)  # type: ignore # noqa: F821
