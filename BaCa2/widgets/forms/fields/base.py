from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from widgets.forms.fields.course import *


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


class AlphanumericField(forms.CharField):
    """
    Form field which accepts only strings consisting of alphanumeric characters.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            validators=[AlphanumericField.validate_syntax],
            **kwargs
        )

    @staticmethod
    def validate_syntax(value: str) -> None:
        """
        Checks if the value contains only alphanumeric characters.

        :param value: Value to be validated.
        :type value: str
        :raises: ValidationError if the value contains characters other than alphanumeric
            characters.
        """
        if any(not c.isalnum() for c in value):
            raise forms.ValidationError(_('This field can only contain alphanumeric characters.'))


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
