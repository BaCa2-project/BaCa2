from random import choice

import yaml


def random_string(length: int, array):
    return ''.join(choice(array) for _ in range(length))


def yaml_coerce(value):
    if isinstance(value, str):
        return yaml.load('dummy: ' + value, Loader=yaml.SafeLoader)['dummy']

    return value
