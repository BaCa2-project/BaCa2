from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale'  # noqa: F821
]

LANGUAGES = [
    ('pl', _('Polish')),
    ('en', _('English')),
]

for path in LOCALE_PATHS:
    _auto_create_dirs.add_dir(path)  # noqa: F821
