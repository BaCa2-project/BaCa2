from django import forms

from main.models import Course


class FormWidget:
    def __init__(self,
                 form: forms.Form,
                 button_text: str = 'Submit',
                 display_non_field_validation: bool = True,
                 display_field_errors: bool = True,
                 floating_labels: bool = True,) -> None:
        self.form = form
        self.button_text = button_text
        self.display_non_field_validation = display_non_field_validation
        self.display_field_errors = display_field_errors
        self.floating_labels = floating_labels

    def get_context(self) -> dict:
        context = {
            'form': self.form,
            'button_text': self.button_text,
            'display_non_field_errors': self.display_non_field_validation,
            'display_field_errors': self.display_field_errors,
            'floating_labels': self.floating_labels,
        }
        return context


class NewCourseForm(forms.Form):
    name = forms.CharField(
        label='Nazwa kursu',
        max_length=Course._meta.get_field('name').max_length,
        required=True
    )
    short_name = forms.CharField(
        label='Skrócona nazwa kursu',
        max_length=Course._meta.get_field('short_name').max_length,
        required=False,
        widget=forms.HiddenInput()
    )
