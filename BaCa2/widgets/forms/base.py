from django import forms
from typing import Any, Dict, List

from main.models import Course
from widgets.base import Widget


def get_field_validation_status(field_cls: str,
                                value: Any,
                                required: bool = False,
                                min_length: int or bool = False) -> Dict[str, str or List[str]]:
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
                        'messages': ['To pole jest wymagane.']}

            if required and min_length and len(value) < min_length:
                return {'status': 'error',
                        'messages': [f'Wymagane jest minimum {min_length} znaków.']}

            elif min_length and len(value) < min_length:
                return {'status': 'error',
                        'messages': [f'Wymagane jest minimum {min_length} znaków.']}

            return {'status': 'ok'}
        except forms.ValidationError as e:
            return {'status': 'error',
                    'messages': e.messages}
    else:
        return {'status': 'ok'}


class FormWidget(Widget):
    def __init__(self,
                 name: str,
                 form: forms.Form,
                 button_text: str = 'Submit',
                 display_non_field_validation: bool = True,
                 display_field_errors: bool = True,
                 floating_labels: bool = True,
                 toggleable_fields: List[str] = None,
                 toggleable_fields_params: Dict[str, Dict[str, str]] = None,
                 live_validation: bool = True,) -> None:
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
                params['button_text_on'] = 'Przydziel Automatycznie'
            if 'button_text_off' not in params.keys():
                params['button_text_off'] = 'Przydziel Ręcznie'

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
    form_name = forms.CharField(
        label='Nazwa formularza',
        max_length=100,
        widget=forms.HiddenInput(),
        required=True,
        initial='form'
    )


class CourseShortName(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(
            label='Kod kursu',
            min_length=2,
            max_length=Course._meta.get_field('short_name').max_length,
            validators=[CourseShortName.validate_uniqueness, CourseShortName.validate_syntax],
            required=False,
            **kwargs
        )

    @staticmethod
    def validate_uniqueness(value: str):
        if Course.objects.filter(short_name=value.lower()).exists():
            raise forms.ValidationError('Kod kursu jest już zajęty.')

    @staticmethod
    def validate_syntax(value: str):
        if any(not (c.isalnum() or c == '_') for c in value):
            raise forms.ValidationError('Kod kursu może zawierać tylko litery,cyfry i znaki \
                                        podkreślenia.')


class NewCourseForm(BaCa2Form):
    name = forms.CharField(
        label='Nazwa kursu',
        min_length=5,
        max_length=Course._meta.get_field('name').max_length,
        required=True
    )
    short_name = CourseShortName()

    def __init__(self, **kwargs):
        super().__init__(initial={'form_name': 'new_course_form'}, **kwargs)


class NewCourseFormWidget(FormWidget):
    def __init__(self, form: NewCourseForm = None, **kwargs):
        if not form:
            form = NewCourseForm()

        super().__init__(
            form=form,
            button_text='Dodaj kurs',
            toggleable_fields=['short_name'],
            **kwargs
        )
