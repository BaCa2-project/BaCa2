import os

from .misc import yaml_coerce


def get_settings_from_env(prefix: str):
    """Get settings from environment variables with given prefix"""
    return {
        key[len(prefix):]: yaml_coerce(os.getenv(key))
        for key in os.environ
        if key.startswith(prefix)
    }
