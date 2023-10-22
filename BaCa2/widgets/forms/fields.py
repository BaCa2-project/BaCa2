from typing import (List, Dict, Any)

from django import forms
from django.utils.translation import gettext_lazy as _

from main.models import Course
from widgets.listing import TableWidget


# ------------------------------------- Field validation --------------------------------------- #

def get_field_validation_status(field_cls: str,
                                value: Any,
                                required: bool = False,
                                min_length: int | bool = False) -> Dict[str, str or List[str]]:
    """
    Runs validators for a given field class and value and returns a dictionary containing the status
    of the validation and a list of error messages if the validation failed.

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

            if required and min_length and len(value) < min_length:
                return {'status': 'error',
                        'messages': [_(f'Minimum length is {min_length} characters.')]}

            elif min_length and len(value) < min_length:
                return {'status': 'error',
                        'messages': [_(f'Minimum length is {min_length} characters.')]}

            return {'status': 'ok'}
        except forms.ValidationError as e:
            return {'status': 'error',
                    'messages': e.messages}
    else:
        return {'status': 'ok'}


# ------------------------------------- Custom field types ------------------------------------- #

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

    def __init__(self, table_widget: TableWidget, **kwargs) -> None:
        """
        :param table_widget: Table widget to use for record selection.
        :type table_widget: TableWidget

        :raises TableSelectFieldException: If the table widget does not have record selection
        enabled.
        """
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
        """
        Get a list of ids of targeted model instances from a table select field of a form.

        :param form: Form containing the table select field.
        :type form: forms.Form
        :param field_name: Name of the table select field.
        :type field_name: str

        :return: List of ids of targeted model instances or `None` if it was not provided in the
            request
        :rtype: List[int] | None
        """
        targets: str = form.cleaned_data.get(field_name, None)

        if not targets:
            return None

        return [int(target_id) for target_id in targets.split(',')]


# ------------------------------ Model/form specific field classes ----------------------------- #

class CourseShortName(forms.CharField):
    """
    Custom form field for :py:class:`main.Course` short name. Its validators check if the course
    code is unique and if it contains only alphanumeric characters and underscores.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            label=_('Course code'),
            min_length=3,
            max_length=Course._meta.get_field('short_name').max_length,
            validators=[CourseShortName.validate_uniqueness, CourseShortName.validate_syntax],
            required=False,
            **kwargs
        )

    @staticmethod
    def validate_uniqueness(value: str) -> None:
        """
        Checks if the course short name is unique.

        :param value: Course short name.
        :type value: str

        :raises: ValidationError if the course short name is not unique.
        """
        if Course.objects.filter(short_name=value.lower()).exists():
            raise forms.ValidationError(_('Course with this code already exists.'))

    @staticmethod
    def validate_syntax(value: str) -> None:
        """
        Checks if the course short name contains only alphanumeric characters and underscores.

        :param value: Course short name.
        :type value: str

        :raises: ValidationError if the course short name contains characters other than
            alphanumeric characters and.
        """
        if any(not (c.isalnum() or c == '_') for c in value):
            raise forms.ValidationError(_('Course code can only contain alphanumeric characters and'
                                          'underscores.'))
