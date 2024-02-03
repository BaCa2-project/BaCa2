from core.tools.collections import deep_update
from core.tools.env_settings import get_settings_from_env

deep_update(globals(), get_settings_from_env(ENVVAR_SETTINGS_PREFIX))   # noqa: F821
