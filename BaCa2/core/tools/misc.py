import uuid
from random import choice
from threading import Lock
from typing import Tuple

import yaml

random_id_access_lock = Lock()


def random_string(length: int, array):
    return ''.join(choice(array) for _ in range(length))


def yaml_coerce(value):
    if isinstance(value, str):
        return yaml.load('dummy: ' + value, Loader=yaml.SafeLoader)['dummy']

    return value


def random_id():
    with random_id_access_lock:
        return str(uuid.uuid4())


def str_to_datetime(date_str: str, dt_format: str = None):
    from datetime import datetime

    from django.conf import settings
    from django.utils import timezone

    if not dt_format:
        dt_format = settings.DATETIME_FORMAT

    result = datetime.strptime(date_str, dt_format)
    result = timezone.make_aware(result, timezone.get_current_timezone())

    return result


def try_getting_name_from_email(email: str) -> Tuple[str, str]:
    prefix = email.split('@')[0]
    try:
        return prefix.split('.')[0], prefix.split('.')[1]
    except ValueError:
        return prefix, ''
