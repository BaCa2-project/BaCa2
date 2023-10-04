from typing import Any

from django import template


register = template.Library()


@register.filter
def get_item(dictionary: dict, key: Any):
    return dictionary.get(key)


@register.simple_tag
def validation_status(field, value):
    return field.validation_status(value)
