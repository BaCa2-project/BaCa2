from core.tools.env_settings import get_settings_from_env
from core.tools.collections import deep_update

deep_update(globals(), get_settings_from_env(ENVVAR_SETTINGS_PREFIX))  # type: ignore # noqa: F821
