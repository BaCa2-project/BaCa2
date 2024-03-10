STATIC_URL = '/static/'
STATIC_ROOT = '/home/zyndram/core/static/'
STATICFILES_DIRS = (
    BASE_DIR / 'assets',  # noqa: F821
    TASK_DESCRIPTIONS_DIR,  # noqa: F821
    SUBMITS_DIR,  # noqa: F821
)
for d in STATICFILES_DIRS:
    _auto_create_dirs.assert_exists_dir(d)  # noqa: F821
