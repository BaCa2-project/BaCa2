from __future__ import annotations

import json
from abc import ABC
from typing import List

from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from course.routing import InCourse
from main.models import Course
from util.models import model_cls
from util.models_registry import ModelsRegistry

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
                + f'{", ".join(cls.ACCEPTED_CHARS)}.')  # noqa: Q000


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
                 f'{", ".join(self.queryset)}.')  # noqa: Q000


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
                 f'{", ".join([str(elem) for elem in self.queryset])}.')  # noqa: Q000


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


# ----------------------------------------- file fields ---------------------------------------- #

class FileUploadField(forms.FileField):
    """
    Custom file upload field extending the Django `FileField`. The field can be configured to
    accept only files with specific extensions.
    """

    def __init__(self,
                 allowed_extensions: List[str] = None,
                 **kwargs) -> None:
        """
        :param allowed_extensions: List of allowed file extensions. If not provided, all extensions
            are allowed.
        :type allowed_extensions: List[str]
        :param kwargs: Additional keyword arguments for the field.
        :type kwargs: dict
        """
        validators = kwargs.get('validators', [])

        if allowed_extensions:
            self.allowed_extensions = allowed_extensions
            validators.append(FileExtensionValidator(allowed_extensions))

        kwargs['validators'] = validators
        super().__init__(**kwargs)


# --------------------------------------- date-time fields ------------------------------------- #

class DateTimeField(forms.DateTimeField):
    """
    Custom date-time field extending the Django `DateTimeField` class to allow for proper rendering
    with a date and/or time picker. The field can be configured to display a date picker, a time
    picker or both. The time picker can be configured to have a custom time step.
    """

    def __init__(self,
                 *,
                 datepicker: bool = True,
                 timepicker: bool = True,
                 time_step: int = 30,
                 **kwargs) -> None:
        """
        : param datepicker: Whether to display a date picker.
        : type datepicker: bool
        : param timepicker: Whether to display a time picker.
        : type timepicker: bool
        : param time_step: Time step for the time picker in minutes. Only used if the time picker is
            enabled. Defaults to 30.
        : type time_step: int
        : param kwargs: Additional keyword arguments for the field.
        : type kwargs: dict
        """
        if not datepicker and not timepicker:
            raise ValueError('At least one of datepicker and timepicker must be enabled.')

        self.special_field_type = 'datetime'
        self.timepicker = json.dumps(timepicker)
        self.datepicker = json.dumps(datepicker)
        self.time_step = time_step

        if datepicker and timepicker:
            kwargs.setdefault('input_formats', ['%Y-%m-%d %H:%M'])
            self.format = 'Y-m-d H:i'
        elif datepicker:
            kwargs.setdefault('input_formats', ['%Y-%m-%d'])
            self.format = 'Y-m-d'
        elif timepicker:
            kwargs.setdefault('input_formats', ['%H:%M'])
            self.format = 'H:i'

        super().__init__(**kwargs)

    def __setattr__(self, key, value):
        """
        Intercepts the setting of the `initial` attribute to convert the value to a string using the
        expected input format.
        """
        if key == 'initial':
            if value:
                value = value.strftime(self.input_formats[0])
        super().__setattr__(key, value)

    def widget_attrs(self, widget) -> dict:
        """
        Sets the appropriate class attribute for the widget needed for proper rendering.
        """
        attrs = super().widget_attrs(widget)
        attrs['class'] = 'form-control date-field'
        return attrs


# ---------------------------------------- choice fields --------------------------------------- #

class ChoiceField(forms.ChoiceField):
    """
    Custom choice field extending the Django `ChoiceField` class to allow for proper rendering.
    Adds option to specify a default placeholder option which is displayed when no option is
    selected.
    """
    def __init__(self,
                 placeholder_default_option: bool = True,
                 placeholder_option: str = '---',
                 **kwargs):
        """
        :param placeholder_default_option: Whether to display the placeholder option when no option
            is selected. If set to `False`, the placeholder option will not be added.
        :type placeholder_default_option: bool
        :param placeholder_option: Label of the placeholder option to be displayed when no option is
            selected. If not provided defaults to `---`.
        :type placeholder_option: str
        """
        self.special_field_type = 'choice'
        self.placeholder_default_option = placeholder_default_option
        self.placeholder_option = placeholder_option
        super().__init__(**kwargs)

    def widget_attrs(self, widget) -> dict:
        """
        Sets the appropriate class attribute for the widget needed for proper rendering and adds
        the placeholder option data attribute if necessary.
        """
        attrs = super().widget_attrs(widget)
        attrs['class'] = 'form-select choice-field'
        if self.placeholder_default_option:
            attrs['class'] += ' placeholder-option'
            attrs['data-placeholder-option'] = self.placeholder_option
        return attrs


class ModelChoiceField(ChoiceField):
    """
    Form choice field which fetches its choices from a model view using the provided url. Allows to
    specify custom label and value format strings for the choices, which can use the fields of
    records fetched from the model view. The label format string is used to generate the option
    labels, while the value format string is used to generate the associated values (sent in the
    POST request).
    """

    def __init__(self,
                 data_source_url: str,
                 label_format_string: str,
                 value_format_string: str = '[[id]]',
                 placeholder_option: str = '---',
                 loading_placeholder_option: str = '',
                 **kwargs) -> None:
        """
        :param data_source_url: URL to fetch the choice options from. Should return a JSON response
            with a `data` array containing record dictionaries. Use the `get_url` method of the
            model view associated with desired model to generate the URL.
        :type data_source_url: str
        :param label_format_string: Format string used to generate the option labels. Can use the
            fields of records fetched from the model view with double square brackets notation
            (e.g. `[[field_name]]`).
        :type label_format_string: str
        :param value_format_string: Format string used to generate the associated values. Can use
            the fields of records fetched from the model view with double square brackets
            notation. Defaults to `[[id]]`.
        :type value_format_string: str
        :param placeholder_option: Placeholder option label to be displayed when no option is
            selected. If not provided defaults to `---`.
        :type placeholder_option: str
        :param loading_placeholder_option: Placeholder option label to be displayed while the
            choices are being fetched. If not provided defaults to `Loading...`.
        :type loading_placeholder_option: str
        """
        self._data_source_url = data_source_url
        self.label_format_string = label_format_string
        self.value_format_string = value_format_string
        if not loading_placeholder_option:
            loading_placeholder_option = _('Loading...')
        self.loading_placeholder_option = loading_placeholder_option
        super().__init__(placeholder_default_option=True,
                         placeholder_option=placeholder_option,
                         **kwargs)

    @property
    def data_source_url(self) -> str:
        return self._data_source_url

    @data_source_url.setter
    def data_source_url(self, value: str) -> None:
        self._data_source_url = value
        self.widget.attrs.update({'data-source-url': value})

    def widget_attrs(self, widget) -> dict:
        attrs = super().widget_attrs(widget)
        attrs['class'] += ' model-choice-field'
        attrs['data-loading-option'] = self.loading_placeholder_option
        attrs['data-source-url'] = self._data_source_url
        attrs['data-label-format-string'] = self.label_format_string
        attrs['data-value-format-string'] = self.value_format_string
        return attrs

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(_('This field is required.'))
        # TODO: add proper validation for the field
