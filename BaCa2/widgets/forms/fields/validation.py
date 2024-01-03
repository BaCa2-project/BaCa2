from __future__ import annotations

from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from widgets.forms.course import *


def get_field_validation_status(form_cls: str,
                                field_name: str,
                                value: Any,
                                min_length: int | bool = False) -> Dict[str, str or List[str]]:
    """
    Runs validators for a given field class and value and returns a dictionary containing the status
    of the validation and a list of error messages if the validation has failed.

    :param form_cls: Name of the form class containing the field.
    :type form_cls: str
    :param field_name: Name of the field.
    :type field_name: str
    :param value: Value to be validated.
    :type value: Any
    :param min_length: Minimum length of the value, set to `False` if not defined.
    :type min_length: int | bool
    :return: Dictionary containing the status of the validation and a list of error messages if the
        validation failed.
    :rtype: Dict[str, str or List[str]]
    """
    if value is None:
        value = ''
    if min_length is None:
        min_length = False

    field = eval(form_cls)()[field_name].field

    min_length = int(min_length) if min_length else False

    if hasattr(field, 'clean') and callable(field.clean):
        try:
            field.clean(value)

            if min_length and len(value) < min_length:
                if min_length == 1:
                    return {'status': 'error',
                            'messages': [_('This field cannot be empty.')]}
                else:
                    return {'status': 'error',
                            'messages': [_('This field must contain at least '
                                           f'{min_length} characters.')]}

            return {'status': 'ok'}
        except forms.ValidationError as e:
            return {'status': 'error',
                    'messages': e.messages}
    else:
        return {'status': 'ok'}
