from typing import Any, Dict, List

from django import forms
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget


def get_field_validation_status(field_cls: str,
                                value: Any,
                                required: bool = False,
                                min_length: int | bool = False) -> Dict[str, str or List[str]]:
    """
    Runs validators for a given field class and value and returns a dictionary containing the status of the validation
    and a list of error messages if the validation failed.

    :param field_cls: Field class to be used for validation.
    :type field_cls: str
    :param value: Value to be validated.
    :type value: Any
    :param required: Whether the field is required.
    :type required: bool
    :param min_length: Minimum length of the value, set to `False` if not defined.
    :type min_length: int | bool

    :return: Dictionary containing the status of the validation and a list of error messages if the validation failed.
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


class FormWidget(Widget):
    """
    Base widget for forms. Responsible for generating the context dictionary necessary for rendering the form. The
    default template used for rendering the form is `BaCa2/templates/widget_templates/form_default.html`. FormWidget
    __init__ method arguments control the rendered form's behaviour and appearance.
    """

    def __init__(self,
                 name: str,
                 form: forms.Form,
                 button_text: str = _('Submit'),
                 display_non_field_validation: bool = True,
                 display_field_errors: bool = True,
                 floating_labels: bool = True,
                 toggleable_fields: List[str] = None,
                 toggleable_fields_params: Dict[str, Dict[str, str]] = None,
                 live_validation: bool = True,) -> None:
        """
        :param name: Name of the widget. Should be unique within the scope of one view.
        :type name: str
        :param form: django form object to base the widget on. Should inherit from BaCa2Form.
        :type form: forms.Form
        :param button_text: Text to be displayed on the submit button.
        :type button_text: str
        :param display_non_field_validation: Whether to display non-field validation errors.
        :type display_non_field_validation: bool
        :param display_field_errors: Whether to display field specific errors. If `True`, field specific errors will be
            displayed below their corresponding fields.
        :type display_field_errors: bool
        :param floating_labels: Whether to use floating labels for the form fields.
        :type floating_labels: bool
        :param toggleable_fields: List of names of fields that should be toggleable. This list should only contain
            fields that are not required.
        :type toggleable_fields: List[str]
        :param toggleable_fields_params: Dictionary containing parameters for toggleable fields. The keys of the
            dictionary should be the names of the toggleable fields. The values should be dictionaries containing the
            parameters for the toggleable field. The following parameters are supported:
            `button_text_on` - text to be displayed on the toggle button when the field is in the "on" state,
            `button_text_off` - text to be displayed on the toggle button when the field is in the "off" state.
            If the parameters are not specified, the default values for the supported parameters will be used.
        :type toggleable_fields_params: Dict[str, Dict[str, str]]
        :param live_validation: Whether to perform live validation of the form fields. If `True`, the form will be
            validated on every change of the form fields. Validation results will be displayed below the corresponding
            fields or in form of a green checkmark if the field is valid.
        :type live_validation: bool
        """
        super().__init__(name)
        self.form = form
        self.form_cls = form.__class__.__name__
        self.button_text = button_text
        self.display_non_field_validation = display_non_field_validation
        self.display_field_errors = display_field_errors
        self.floating_labels = floating_labels
        self.live_validation = live_validation

        if not toggleable_fields:
            toggleable_fields = []
        self.toggleable_fields = toggleable_fields

        if not toggleable_fields_params:
            toggleable_fields_params = {}
        self.toggleable_fields_params = toggleable_fields_params

        for field in toggleable_fields:
            if field not in toggleable_fields_params.keys():
                toggleable_fields_params[field] = {}
        for params in toggleable_fields_params.values():
            if 'button_text_on' not in params.keys():
                params['button_text_on'] = _('Generate Automatically')
            if 'button_text_off' not in params.keys():
                params['button_text_off'] = _('Enter Manually')

        self.field_classes = {
            field_name: self.form.fields[field_name].__class__.__name__ for field_name in self.form.fields.keys()
        }

        self.field_required = {
            field_name: self.form.fields[field_name].required for field_name in self.form.fields.keys()
        }

        self.field_min_length = {}
        for field_name in self.form.fields.keys():
            if hasattr(self.form.fields[field_name], 'min_length'):
                self.field_min_length[field_name] = self.form.fields[field_name].min_length
            else:
                self.field_min_length[field_name] = False

    def get_context(self) -> dict:
        context = {
            'form': self.form,
            'form_cls': self.form_cls,
            'button_text': self.button_text,
            'display_non_field_errors': self.display_non_field_validation,
            'display_field_errors': self.display_field_errors,
            'floating_labels': self.floating_labels,
            'toggleable_fields': self.toggleable_fields,
            'toggleable_fields_params': self.toggleable_fields_params,
            'field_classes': self.field_classes,
            'field_required': self.field_required,
            'field_min_length': self.field_min_length,
            'live_validation': self.live_validation,
        }
        return context


class BaCa2Form(forms.Form):
    """
    Base form for all forms in the BaCa2 system. Contains shared, hidden fields
    """

    #: Form name used to identify the form for views which may receive post data from more than one form.
    form_name = forms.CharField(
        label=_('Form name'),
        max_length=100,
        widget=forms.HiddenInput(),
        required=True,
        initial='form'
    )
