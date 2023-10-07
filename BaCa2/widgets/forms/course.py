from django import forms

from main.models import Course
from . import *


class CourseShortName(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(
            label='Kod kursu',
            min_length=2,
            max_length=Course._meta.get_field('short_name').max_length,
            validators=[CourseShortName.validate_uniqueness],
            **kwargs
        )

    @staticmethod
    def validate_uniqueness(value):
        if Course.objects.filter(short_name=value).exists():
            raise forms.ValidationError('Kod kursu jest już zajęty.')


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
            name='new_course_form_widget',
            form=form,
            button_text='Dodaj kurs',
            toggleable_fields=['short_name'],
            **kwargs
        )
