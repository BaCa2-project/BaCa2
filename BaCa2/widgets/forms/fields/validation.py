from __future__ import annotations

from typing import Dict, List

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from widgets.forms.course import *
from widgets.forms.main import *
from widgets.forms.test import *


def get_field_validation_status(request: HttpRequest,
                                form_cls: str,
                                field_name: str,
                                value: str,
                                min_length: int | bool = False) -> Dict[str, str or List[str]]:
    """
    Runs validators for a given field class and value and returns a dictionary containing the status
    of the validation and a list of error messages if the validation has failed.

    :param request: The field validation request.
    :type request: HttpRequest
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

    reconstruct_meth = getattr(eval(form_cls), 'reconstruct', None)

    if reconstruct_meth and callable(reconstruct_meth):
        form = reconstruct_meth(request)
    else:
        form = eval(form_cls)(data=request.POST)

    field = form[field_name].field
    min_length = int(min_length) if min_length else False

    if hasattr(field.widget, 'input_type') and field.widget.input_type == 'file':
        return _get_file_field_validation_status(field, value)

    if hasattr(field, 'clean') and callable(field.clean):
        try:
            field.clean(value)

            if min_length and len(value) < min_length:
                if min_length == 1:
                    return {'status': 'error',
                            'messages': [_('This field cannot be empty.')]}
                else:
                    if len(value) == 0 and not field.widget.is_required:
                        return {'status': 'ok'}

                    return {'status': 'error',
                            'messages': [_('This field must contain at least '
                                           f'{min_length} characters.')]}

            return {'status': 'ok'}
        except forms.ValidationError as e:
            return {'status': 'error',
                    'messages': e.messages}
    else:
        return {'status': 'ok'}


def _get_file_field_validation_status(field: forms.FileField,
                                      value: str) -> Dict[str, str or List[str]]:
    if field.widget.is_required and not value:
        return {'status': 'error',
                'messages': [_('This field is required.')]}
    elif not value:
        return {'status': 'ok'}

    validate_extensions = False
    allowed_extensions = []

    for validator in field.validators:
        if hasattr(validator, 'allowed_extensions'):
            validate_extensions = True
            allowed_extensions = validator.allowed_extensions

    if validate_extensions:
        extension = value.split('.')[-1]
        if extension not in allowed_extensions:
            return {'status': 'error',
                    'messages': [_('This file type is not allowed. Supported file types: ') +
                                 ', '.join(allowed_extensions)]}

    return {'status': 'ok'}
