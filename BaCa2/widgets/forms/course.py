from typing import Dict

from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

from main.models import Course
from widgets.forms.base import (BaCa2Form, FormWidget, FormElementGroup, FormConfirmationPopup,
                                BaCa2ModelForm, ModelFormPostTarget)
from widgets.forms.fields.course import CourseShortName


class CreateCourseForm(BaCa2ModelForm):
    """
    Form for creating new :py:class:`main.Course` objects.
    """

    MODEL = Course
    ACTION = Course.BasicAction.ADD

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
        min_length=1,
        max_length=Course._meta.get_field('USOS_course_code').max_length,
        required=False
    )
    #: Term code of the course in the USOS system.
    USOS_term_code = forms.CharField(
        label=_('USOS term code'),
        min_length=1,
        max_length=Course._meta.get_field('USOS_term_code').max_length,
        required=False
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        try:
            Course.objects.create_course(
                name=request.POST.get('name'),
                short_name=request.POST.get('short_name'),
                usos_course_code=request.POST.get('USOS_course_code'),
                usos_term_code=request.POST.get('USOS_term_code')
            )
        except Exception as e:
            return {'message': str(e)}

        return {'message': _('Course created successfully')}

    @classmethod
    def handle_invalid_request(cls, request) -> Dict[str, str]:
        return {}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        return {}


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
            post_target=ModelFormPostTarget(Course),
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


class DeleteCourseForm(BaCa2Form):
    """
    Form for deleting existing :py:class:`main.Course` objects.
    """

    #: ID of the course to be deleted.
    course_id = forms.IntegerField(
        label=_('Course ID'),
        widget=forms.HiddenInput(),
        required=True
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        try:
            Course.objects.delete_course(request.POST.get('course_id'))
        except Exception as e:
            return {'message': str(e)}

        return {'message': _('Course deleted successfully')}

    @classmethod
    def handle_invalid_request(cls, request) -> Dict[str, str]:
        return {}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        return {}


class DeleteCourseFormWidget(FormWidget):
    def __init__(self, form: DeleteCourseForm = None, **kwargs) -> None:
        if not form:
            form = DeleteCourseForm()

        super().__init__(
            name='delete_course_form_widget',
            form=form,
            post_target=ModelFormPostTarget(Course),
            button_text=_('Delete course'),
            confirmation_popup=FormConfirmationPopup(
                title=_('Confirm course deletion'),
                description=_(
                    'Are you sure you want to delete this course? This action cannot be undone.'
                ),
                confirm_button_text=_('Delete course'),
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
