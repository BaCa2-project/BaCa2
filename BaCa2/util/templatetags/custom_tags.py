import importlib
from typing import Any

from django import template

register = template.Library()


@register.filter
def get_item(dictionary: dict, key: Any):
    return dictionary.get(key)


@register.filter
def is_instance_of(value, class_path):
    path = class_path.split('.')
    module_path = '.'.join(path[:-1])
    class_name = path[-1]

    try:
        module = importlib.import_module(module_path)
        class_obj = getattr(module, class_name)
        return isinstance(value, class_obj)
    except (ImportError, AttributeError):
        return False


@register.simple_tag
def validation_status(field, value):
    return field.validation_status(value)


@register.filter
def get_form_field(form, field_name):
    return form[field_name]
