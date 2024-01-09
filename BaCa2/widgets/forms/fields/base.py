from __future__ import annotations

from typing import List, TYPE_CHECKING
from abc import ABC

from django.utils.translation import gettext_lazy as _
from django import forms

from util.models import model_cls
from util.models_registry import ModelsRegistry
from main.models import Course
from course.routing import InCourse

if TYPE_CHECKING:
    from widgets.listing.columns import Column
    from widgets.listing.data_sources import TableDataSource


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

        if not kwargs.get('strip', False):
            kwargs['strip'] = False

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


# ---------------------------------------- array fields ---------------------------------------- #

class CharArrayField(forms.CharField):
    """
    Form field used to store a comma-separated list of strings. If provided with a queryset, the
    field will validate that all strings in the list are present in it. It can also receive a list
    of item validators which will be used to validate each string in the list.

    See also:
        - :class:`IntegerArrayField`
    """

    def __init__(self,
                 queryset: List[str] = None,
                 item_validators: List[callable] = None,
                 **kwargs) -> None:
        """
        :param queryset: List of strings which are accepted by the field. If not provided, all
            strings are accepted.
        :type queryset: List[str]
        :param item_validators: List of validators which will be used to validate each string in
            the list.
        :type item_validators: List[callable]
        :param kwargs: Additional keyword arguments for the field.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self.queryset = queryset
        self.item_validators = item_validators or []

    def to_python(self, value: str) -> List[str]:
        """
        Converts the value to a list of strings.

        :param value: Value to be converted.
        :type value: str
        :return: List of strings.
        :rtype: List[str]
        :raises: ValidationError if the method encounters a value, type or attribute error while
            converting the value.
        """
        value = super().to_python(value)
        if not value:
            return []
        try:
            return value.split(',')
        except (ValueError, TypeError, AttributeError):
            raise forms.ValidationError(_('This field must be a comma-separated list of strings.'))

    def validate(self, value: List[str]) -> None:
        """
        Validates the value by running all item validators on each string in the list and checking
        if all strings are present in the queryset.

        :param value: Value to be validated.
        :type value: List[str]
        :raises: ValidationError if the value does not pass validation.
        """
        super().validate(value)

        for validator in self.item_validators:
            for elem in value:
                validator(elem)

        for elem in value:
            if not elem:
                raise forms.ValidationError(_('This field cannot contain empty strings.'))

        if self.queryset and any(elem not in self.queryset for elem in value):
            raise forms.ValidationError(self.queryset_validation_error_message())

    def queryset_validation_error_message(self) -> str:
        """
        Returns a validation error message for the field when the value does not pass queryset
        validation.

        :return: Error message for the field.
        :rtype: str
        """
        return _('This field must be a comma-separated list of strings from the following list: '
                 f'{", ".join(self.queryset)}.')


class IntegerArrayField(CharArrayField):
    """
    Form field used to store a comma-separated list of integers. If provided with a queryset, the
    field will validate that all integers in the list are present in it. It can also receive a list
    of item validators which will be used to validate each integer in the list.

    See also:
        - :class:`CharArrayField`
        - :class:`ModelArrayField`
    """

    def __init__(self,
                 queryset: List[int] = None,
                 item_validators: List[callable] = None,
                 **kwargs) -> None:
        """
        :param queryset: List of integers which are accepted by the field. If not provided, all
            integers are accepted.
        :type queryset: List[int]
        :param item_validators: List of validators which will be used to validate each integer in
            the list.
        :type item_validators: List[callable]
        :param kwargs: Additional keyword arguments for the field.
        :type kwargs: dict
        """
        super().__init__(queryset, item_validators, **kwargs)

    def to_python(self, value: str) -> List[int]:
        """
        Converts the value to a list of integers.

        :param value: Value to be converted.
        :type value: str
        :return: List of integers.
        :rtype: List[int]
        :raises: ValidationError if the method encounters a value, type or overflow error while
            converting the value.
        """
        try:
            return [int(elem) for elem in super().to_python(value)]
        except (ValueError, TypeError, OverflowError):
            raise forms.ValidationError(_('This field must be a comma-separated list of integers.'))

    def queryset_validation_error_message(self) -> str:
        """
        Returns a validation error message for the field when the value does not pass queryset
        validation.

        :return: Error message for the field.
        :rtype: str
        """
        return _('This field must be a comma-separated list of integers from the following list: '
                 f'{", ".join([str(elem) for elem in self.queryset])}.')


class ModelArrayField(IntegerArrayField):
    """
    Form field used to store a comma-separated list of model instance IDs.

    See also:
        - :class:`IntegerArrayField`
    """

    def __init__(self,
                 model: model_cls,
                 item_validators: List[callable] = None,
                 **kwargs) -> None:
        """
        :param model: Model which instance IDs are accepted by the field.
        :type model: Type[models.Model]
        :param item_validators: List of validators which will be used to validate each model
            instance in the list.
        :type item_validators: List[callable]
        :param kwargs: Additional keyword arguments for the field.
        :type kwargs: dict
        """
        super().__init__(item_validators=item_validators, **kwargs)
        self.model = model

    def __getattribute__(self, item):
        """
        Intercepts the `queryset` attribute access to dynamically generate the queryset of model
        instance IDs.
        """
        if item == 'queryset':
            return [instance.id for instance in self.model.objects.all()]
        return super().__getattribute__(item)

    def queryset_validation_error_message(self) -> str:
        """
        Returns a validation error message for the field when the value does not pass queryset
        validation.

        :return: Error message for the field.
        :rtype: str
        """
        return _(f'This field must be a comma-separated list of {self.model.__name__} IDs')


class CourseModelArrayField(ModelArrayField):
    """
    Form field used to store a comma-separated list of model instance IDs for a course database
    model class.

    See also:
        - :class:`ModelArrayField`
    """

    def __init__(self,
                 model: model_cls,
                 course: int | str | Course = None,
                 item_validators: List[callable] = None,
                 **kwargs) -> None:
        """
        :param model: Model which instance IDs are accepted by the field.
        :type model: Type[models.Model]
        :param course: Course to which the model instances belong. Can be specified as a course
            instance, course ID or course short name.
        :type course: int | str | Course
        :param item_validators: List of validators which will be used to validate each model
            instance in the list.
        :type item_validators: List[callable]
        :param kwargs: Additional keyword arguments for the field.
        :type kwargs: dict
        """
        super().__init__(model=model, item_validators=item_validators, **kwargs)
        self.course = ModelsRegistry.get_course(course)

    def __getattribute__(self, item):
        """
        Intercepts the `queryset` attribute access to dynamically generate the queryset of model
        instance IDs.
        """
        if item == 'queryset':

            with InCourse(self.course.short_name):
                return [instance.id for instance in self.model.objects.all()]
        return super().__getattribute__(item)


# ------------------------------------- table select field ------------------------------------- #

class TableSelectField(forms.CharField):
    """
    Form field used to store IDs of records selected in a table widget. The field is hidden and in
    its place the stored table widget is rendered. The field is updated live when records are
    selected or deselected in the table widget.

    See also:
        - :class:`TableWidget`
        - :class:`widgets.forms.base.TableWidget`
    """

    def __init__(self, data_source: TableDataSource, cols: List[Column]) -> None:
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
