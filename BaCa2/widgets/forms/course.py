from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

from main.models import Course
from widgets.forms.base import (BaCa2Form, FormWidget, FormElementGroup, FormConfirmationPopup)
from widgets.forms.fields.course import CourseShortName


class CreateCourseForm(BaCa2Form):
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

    def __init__(self, **kwargs) -> None:
        super().__init__(initial={'form_name': 'create_course_form',
                                  'action': 'create'},
                         **kwargs)

    @staticmethod
    def handle_post_request(request):
        pass


class CreateCourseFormWidget(FormWidget):
    """
    Form widget for creating new courses. Built on top of :py:class:`FormWidget`.
    """

    def __init__(self, form: CreateCourseForm = None, **kwargs) -> None:
        """
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: CreateCourseForm
        """
        if not form:
            form = CreateCourseForm()

        super().__init__(
            name='create_course_form_widget',
            form=form,
            post_url=reverse_lazy('main:course-model-view'),
            ajax_post=True,
            button_text=_('Add course'),
            toggleable_fields=['short_name'],
            element_groups=FormElementGroup(
                elements=['USOS_course_code', 'USOS_term_code'],
                name='USOS_data',
                toggleable=True,
                toggleable_params={'button_text_off': _('Add USOS data'),
                                   'button_text_on': _('Create without USOS data')},
                frame=True,
                layout=FormElementGroup.FormElementsLayout.HORIZONTAL
            ),
            confirmation_popup=FormConfirmationPopup(
                title=_('Confirm course creation'),
                description=_(
                    'Are you sure you want to create a new course with the following data?'
                ),
                confirm_button_text=_('Create course'),
                input_summary=True,
                input_summary_fields=['name', 'short_name', 'USOS_course_code', 'USOS_term_code'],
            ),
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
