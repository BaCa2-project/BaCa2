from typing import Any, Dict, List
from abc import ABC

from django.utils.translation import gettext_lazy as _

from widgets.forms.fields.course import *


# -------------------------------------- field validation -------------------------------------- #

def get_field_validation_status(field_cls: str,
                                value: Any,
                                required: bool = False,
                                min_length: int | bool = False) -> Dict[str, str or List[str]]:
    """
    Runs validators for a given field class and value and returns a dictionary containing the status
    of the validation and a list of error messages if the validation has failed.

    :param field_cls: Field class to be used for validation.
    :type field_cls: str
    :param value: Value to be validated.
    :type value: Any
    :param required: Whether the field is required.
    :type required: bool
    :param min_length: Minimum length of the value, set to `False` if not defined.
    :type min_length: int | bool
    :return: Dictionary containing the status of the validation and a list of error messages if the
        validation failed.
    :rtype: Dict[str, str or List[str]]
    """
    if value is None:
        value = ''
    if required is None:
        required = False
    if min_length is None:
        min_length = False

    try:
        field = eval(field_cls)()
    except NameError:
        field = (eval(f'forms.{field_cls}'))()

    min_length = int(min_length) if min_length else False

    if hasattr(field, 'run_validators') and callable(field.run_validators):
        try:
            field.run_validators(value)

            if required and not value:
                return {'status': 'error',
                        'messages': [_('This field is required.')]}

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


# ----------------------------------- restricted char fields ----------------------------------- #

class RestrictedCharField(forms.CharField, ABC):
    """
    Base class for form fields which accept only strings consisting of a restricted set of
    characters.
    """

    #: List of characters accepted by the field.
    ACCEPTED_CHARS = []

    def __init__(self, **kwargs) -> None:
        if 'validators' in kwargs:
            kwargs['validators'].append(self.validate_syntax)
        else:
            kwargs['validators'] = [self.validate_syntax]

        super().__init__(
            **kwargs
        )

    @classmethod
    def validate_syntax(cls, value: str) -> None:
        """
        Checks if the value contains only characters accepted by the field.

        :param value: Value to be validated.
        :type value: str
        :raises: ValidationError if the value contains characters other than those accepted by the
            field.
        """
        if any(c not in cls.ACCEPTED_CHARS for c in value):
            raise forms.ValidationError(cls.syntax_validation_error_message())

    @classmethod
    def syntax_validation_error_message(cls) -> str:
        """
        Returns a validation error message for the field.

        :return: Error message for the field.
        :rtype: str
        """
        return (_('This field can only contain the following characters: ')
                + f'{", ".join(cls.ACCEPTED_CHARS)}.')


class AlphanumericField(RestrictedCharField):
    """
    Form field which accepts only strings consisting of alphanumeric characters.

    See also:
        - :class:`RestrictedCharField`
    """

    @classmethod
    def validate_syntax(cls, value: str) -> None:
        """
        Checks if the value contains only alphanumeric characters.

        :param value: Value to be validated.
        :type value: str
        :raises: ValidationError if the value contains characters other than alphanumeric
            characters.
        """
        if any(not (c.isalnum() or c in cls.ACCEPTED_CHARS) for c in value):
            raise forms.ValidationError(cls.syntax_validation_error_message())

    @classmethod
    def syntax_validation_error_message(cls) -> str:
        """
        Returns a validation error message for the field.

        :return: Error message for the field.
        :rtype: str
        """
        return _('This field can only contain alphanumeric characters.')


class AlphanumericStringField(AlphanumericField):
    """
    Form field which accepts only strings consisting of alphanumeric characters and spaces.

    See also:
        - :class:`AlphanumericField`
    """

    ACCEPTED_CHARS = [' ']

    def __init__(self, **kwargs) -> None:
        super().__init__(
            **kwargs,
            validators=[AlphanumericStringField.validate_trailing_spaces,
                        AlphanumericStringField.validate_double_spaces]
        )

    @staticmethod
    def validate_trailing_spaces(value: str) -> None:
        """
        Checks if the value does not contain trailing spaces.

        :param value: Value to be validated.
        :type value: str
        :raises: ValidationError if the value contains trailing spaces.
        """
        if value and (value[0] == ' ' or value[-1] == ' '):
            raise forms.ValidationError(_('This field cannot contain trailing whitespaces.'))

    @staticmethod
    def validate_double_spaces(value: str) -> None:
        """
        Checks if the value does not contain double spaces.

        :param value: Value to be validated.
        :type value: str
        :raises: ValidationError if the value contains double spaces.
        """
        if '  ' in value:
            raise forms.ValidationError(_('This field cannot contain double spaces.'))

    @classmethod
    def syntax_validation_error_message(cls) -> str:
        """
        Returns a validation error message for the field.

        :return: Error message for the field.
        :rtype: str
        """
        return _('This field can only contain alphanumeric characters and spaces.')


# ------------------------------------- table select field ------------------------------------- #

class TableSelectField(forms.CharField):
    """
    Form field used to store the IDs of the selected rows in a table widget. The field is hidden
    and in its place the stored table widget is rendered. The field is updated live when records
    are selected or deselected in the table widget.
    """

    class TableSelectFieldException(Exception):
        """
        Exception raised when an error occurs in the TableSelectField class.
        """
        pass

    # TODO: Implement TableSelectField with new TableWidget
    """
    def __init__(self, table_widget: TableWidget, **kwargs) -> None:
        
        :param table_widget: Table widget to use for record selection.
        :type table_widget: TableWidget

        :raises TableSelectFieldException: If the table widget does not have record selection
        enabled.
        
        if not table_widget.has_record_method('select'):
            raise TableSelectField.TableSelectFieldException(
                'Table widget used in TableSelectField does not have '
                'record selection enabled.'
            )

        super().__init__(
            label=_('Selected rows IDs'),
            widget=forms.HiddenInput(
                attrs={'class': 'table-select-field', 'data-table-target': table_widget.table_id}
            ),
            initial='',
            **kwargs
        )
        self.table_widget = table_widget.get_context()

    @staticmethod
    def get_target_list(form: forms.Form, field_name: str) -> List[int] | None:
        
        Get a list of ids of targeted model instances from a table select field of a form.

        :param form: Form containing the table select field.
        :type form: forms.Form
        :param field_name: Name of the table select field.
        :type field_name: str

        :return: List of ids of targeted model instances or `None` if it was not provided in the
            request
        :rtype: List[int] | None
        
        targets: str = form.cleaned_data.get(field_name, None)

        if not targets:
            return None

        return [int(target_id) for target_id in targets.split(',')]
    """
