import uuid
from random import choice
from threading import Lock

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
