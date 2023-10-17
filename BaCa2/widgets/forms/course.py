from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

from main.models import Course
from widgets.forms.base import (BaCa2Form, TableSelectField, FormWidget)
from widgets.listing import TableWidget
from main.models import User


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


class NewCourseForm(BaCa2Form):
    """
    Form for creating new :py:class:`main.Course` objects.
    """
    #: New course's name.
    name = forms.CharField(
        label=_('Course name'),
        min_length=5,
        max_length=Course._meta.get_field('name').max_length,
        required=True
    )
    #: New course's short name.
    short_name = CourseShortName()
    #: Subject code of the course in the USOS system.
    USOS_course_code = forms.CharField(
        label=_('USOS course code'),
        max_length=Course._meta.get_field('USOS_course_code').max_length,
        required=False
    )
    #: Term code of the course in the USOS system.
    USOS_term_code = forms.CharField(
        label=_('USOS term code'),
        max_length=Course._meta.get_field('USOS_term_code').max_length,
        required=False
    )
    course_members = TableSelectField(TableWidget(
        name='new_course_table_widget',
        model_cls=User,
        select=True,
        cols=['id', 'first_name', 'last_name', 'email'],
    ), required=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(initial={'form_name': 'create_course_form',
                                  'action': 'create'},
                         **kwargs)


class NewCourseFormWidget(FormWidget):
    """
    Form widget for creating new courses. Built on top of :py:class:`FormWidget`.
    """

    def __init__(self, form: NewCourseForm = None, **kwargs) -> None:
        """
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: NewCourseForm
        """
        if not form:
            form = NewCourseForm()

        super().__init__(
            name='create_course_form_widget',
            form=form,
            post_url=reverse_lazy('main:course-model-view'),
            button_text=_('Add course'),
            toggleable_fields=['short_name', 'USOS_course_code', 'USOS_term_code'],
            **kwargs
        )


class CourseForm(BaCa2Form):
    """
    Base form for all forms used to edit existing :py:class:`main.Course` objects.
    """

    #: ID of the course to be edited. Used to identify the course from which scope the request
    # originates.
    course_id = forms.IntegerField(
        label=_('Course ID'),
        widget=forms.HiddenInput(),
        required=True
    )
