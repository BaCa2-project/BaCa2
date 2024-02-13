import logging
from typing import Dict

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.choices import TaskJudgingMode
from core.tools.files import FileHandler
from course.models import Round, Task
from course.routing import InCourse
from main.models import Course
from widgets.forms.base import (
    BaCa2ModelForm,
    CourseModelFormPostTarget,
    FormElementGroup,
    FormWidget,
    ModelFormPostTarget
)
from widgets.forms.fields import AlphanumericStringField, FileUploadField
from widgets.forms.fields.course import CourseName, CourseShortName, USOSCode
from widgets.popups.forms import SubmitConfirmationPopup

logger = logging.getLogger(__name__)


# ------------------------------------- Course Model Form -------------------------------------- #

class CourseModelForm(BaCa2ModelForm):
    @classmethod
    def is_permissible(cls, request) -> bool:
        return request.user.has_course_permission(cls.ACTION.label, InCourse.get_context_course())


# ---------------------------------------- create course --------------------------------------- #

class CreateCourseForm(BaCa2ModelForm):
    """
    Form used to create a new :class:`Course` object.

    See also:
        - :class:`BaCa2ModelForm`
        - :class:`Course`
    """

    MODEL = Course
    ACTION = Course.BasicAction.ADD

    #: New course's name.
    name = CourseName(label=_('Course name'), required=True)

    #: New course's short name.
    short_name = CourseShortName()

    #: Subject code of the course in the USOS system.
    USOS_course_code = USOSCode(
        label=_('USOS course code'),
        max_length=Course._meta.get_field('USOS_course_code').max_length,
        required=False
    )

    #: Term code of the course in the USOS system.
    USOS_term_code = USOSCode(
        label=_('USOS term code'),
        max_length=Course._meta.get_field('USOS_term_code').max_length,
        required=False
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`Course` object based on the data provided in the request.

        :param request: POST request containing the course data.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        Course.objects.create_course(
            name=request.POST.get('name'),
            short_name=request.POST.get('short_name'),
            usos_course_code=request.POST.get('USOS_course_code'),
            usos_term_code=request.POST.get('USOS_term_code')
        )
        return {'message': _('Course ') + request.POST.get('name') + _(' created successfully')}

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        """
        Returns response message for a request containing invalid data.

        :param request: POST request containing the course data.
        :type request: HttpRequest
        :param errors: Dictionary containing information about the errors found in the form data.
        :type errors: dict
        :return: Dictionary containing an error message preceding the list of errors.
        :rtype: Dict[str, str]
        """
        return {'message': _('Course creation failed due to invalid data. Please correct the '
                             'following errors:')}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        """
        Returns response message for a request from a user without the permission to create new
        courses.

        :param request: POST request containing the course data.
        :type request: HttpRequest
        :return: Dictionary containing an error message.
        :rtype: Dict[str, str]
        """
        return {'message': _('Course creation failed due to insufficient permissions.')}

    @classmethod
    def handle_error(cls, request, error) -> Dict[str, str]:
        """
        Returns response message for a request that failed due to an error other than invalid data
        or insufficient permissions.

        :param request: POST request containing the course data.
        :type request: HttpRequest
        :param error: Error that caused the request to fail.
        :type error: Exception
        :return: Dictionary containing an error message.
        :rtype: Dict[str, str]
        """
        return {'message': 'Course creation failed due to the following error:\n' + str(error)}


class CreateCourseFormWidget(FormWidget):
    """
    Form widget for creating new courses.

    See also:
        - :class:`FormWidget`
        - :class:`CreateCourseForm`
    """

    def __init__(self,
                 request,
                 form: CreateCourseForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: :class:`CreateCourseForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        if not form:
            form = CreateCourseForm()

        super().__init__(
            name='create_course_form_widget',
            request=request,
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
            submit_confirmation_popup=SubmitConfirmationPopup(
                title=_('Confirm course creation'),
                message=_(
                    'Are you sure you want to create a new course with the following data?'
                ),
                confirm_button_text=_('Create course'),
                input_summary=True,
                input_summary_fields=['name', 'short_name', 'USOS_course_code', 'USOS_term_code'],
            ),
            **kwargs
        )


# ---------------------------------------- delete course --------------------------------------- #


class DeleteCourseForm(BaCa2ModelForm):
    """
    Form for deleting existing :py:class:`main.Course` objects.
    """

    MODEL = Course
    ACTION = Course.BasicAction.DEL

    #: ID of the course to be deleted.
    course_id = forms.IntegerField(
        label=_('Course ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True,
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Deletes the course with the ID provided in the request.

        :param request: POST request containing the course ID.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        Course.objects.delete_course(int(request.POST.get('course_id')))
        return {'message': _('Course deleted successfully')}

    @classmethod
    def handle_error(cls, request, error) -> Dict[str, str]:
        """
        Returns response message for a request that failed due to an error other than invalid data
        or insufficient permissions.

        :param request: POST request containing the course ID.
        :type request: HttpRequest
        :param error: Error that caused the request to fail.
        :type error: Exception
        :return: Dictionary containing an error message.
        :rtype: Dict[str, str]
        """
        return {'message': 'Course deletion failed due to the following error:\n' + str(error)}

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        """
        Returns response message for a request containing invalid data.

        :param request: POST request containing the course ID.
        :type request: HttpRequest
        :param errors: Dictionary containing information about the errors found in the form data.
        :type errors: dict
        :return: Dictionary containing an error message preceding the list of errors.
        :rtype: Dict[str, str]
        """
        return {'message': _('Course deletion failed due to invalid data. Please correct the '
                             'following errors:')}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        """
        Returns response message for a request from a user without the permission to delete courses.

        :param request: POST request containing the course ID.
        :type request: HttpRequest
        :return: Dictionary containing an error message.
        :rtype: Dict[str, str]
        """
        return {'message': _('Course deletion failed due to insufficient permissions.')}


class DeleteCourseFormWidget(FormWidget):
    """
    Form widget for deleting courses.

    See also:
        - :class:`FormWidget`
        - :class:`DeleteCourseForm`
    """

    def __init__(self,
                 request,
                 form: DeleteCourseForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: :class:`DeleteCourseForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        if not form:
            form = DeleteCourseForm()

        super().__init__(
            name='delete_course_form_widget',
            request=request,
            form=form,
            post_target=ModelFormPostTarget(Course),
            button_text=_('Delete course'),
            submit_confirmation_popup=SubmitConfirmationPopup(
                title=_('Confirm course deletion'),
                message=_(
                    'Are you sure you want to delete this course? This action cannot be undone.'
                ),
                confirm_button_text=_('Delete course'),
            ),
            **kwargs
        )


# ----------------------------------------- add members ---------------------------------------- #

class AddMembersForm(BaCa2ModelForm):
    MODEL = Course
    ACTION = Course.CourseAction.ADD_MEMBER

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        pass

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        pass

    @classmethod
    def handle_error(cls, request, error: Exception) -> Dict[str, str]:
        pass

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        pass


class AddMembersFormWidget(FormWidget):
    def __init__(self,
                 request,
                 course_id: int,
                 form: AddMembersForm = None,
                 **kwargs) -> None:
        if not form:
            form = AddMembersForm()

        super().__init__(
            name='add_members_form_widget',
            request=request,
            form=form,
            post_target=CourseModelFormPostTarget(model=Course, course=course_id),
            button_text=_('Add members'),
            **kwargs
        )


# --------------------------------------- create round ----------------------------------------- #

class CreateRoundForm(CourseModelForm):
    MODEL = Round
    ACTION = Round.BasicAction.ADD

    name = AlphanumericStringField(label=_('Round name'), required=True)
    start_date = forms.DateTimeField(label=_('Start date'), required=True)
    end_date = forms.DateTimeField(label=_('End date'), required=False)
    deadline_date = forms.DateTimeField(label=_('Deadline date'), required=True)
    reveal_date = forms.DateTimeField(label=_('Reveal date'), required=False)

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        Round.objects.create_round(
            name=request.POST.get('name'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            deadline_date=request.POST.get('deadline_date'),
            reveal_date=request.POST.get('reveal_date')
        )

        return {'message': _('Round ') + request.POST.get('name') + _(' created successfully')}

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        return {'message': _('Round creation failed due to invalid data. Please correct the '
                             'following errors:')}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        return {'message': _('Round creation failed due to insufficient permissions.')}

    @classmethod
    def handle_error(cls, request, error: Exception) -> Dict[str, str]:
        return {'message': 'Round creation failed due to the following error:\n' + str(error)}


class CreateRoundFormWidget(FormWidget):
    def __init__(self,
                 request,
                 course_id: int,
                 form: CreateRoundForm = None,
                 **kwargs) -> None:
        from course.views import RoundModelView

        if not form:
            form = CreateRoundForm()

        super().__init__(
            name='create_round_form_widget',
            request=request,
            form=form,
            post_target=RoundModelView.post_url(course_id=course_id),
            button_text=_('Add round'),
            **kwargs
        )


# ----------------------------------------- create task ---------------------------------------- #

class CreateTaskForm(BaCa2ModelForm):
    MODEL = Task
    ACTION = Task.BasicAction.ADD

    task_name = AlphanumericStringField(
        label=_('Task name (if not provided - will be taken from package)'),
        required=True)
    round_ = AlphanumericStringField(label=_('Round ID (temp)'), required=True)
    points = forms.FloatField(label=_('Points (if not provided - will be taken from package)'),
                              min_value=0)
    package = FileUploadField(label=_('Task package'),
                              required=True,
                              allowed_extensions=['zip'])
    judge_mode = forms.ChoiceField(label=_('Judge mode'),
                                   choices=TaskJudgingMode,
                                   required=True,
                                   )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Creates a new :class:`Task` object based on the data provided in the request.
        Also creates a new :class:`PackageSource` and :class:`PackageInstance` objects based on the
        uploaded package.

        :param request: POST request containing the task data.

        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        from package.models import PackageSource

        task_name = request.POST.get('task_name')
        round_id = request.POST.get('round_')
        points = request.POST.get('points')
        judge_mode = request.POST.get('judge_mode')
        if judge_mode is None:
            judge_mode = TaskJudgingMode.LIN
        else:
            judge_mode = TaskJudgingMode[judge_mode]
        file = FileHandler(settings.UPLOAD_DIR, 'zip', request.FILES['package'])
        file.save()
        try:
            package_instance = PackageSource.objects.create_package_source_from_zip(
                name=task_name,
                zip_file=file.path,
                creator=request.user
            )
        except Exception as e:
            file.delete()
            raise e
        Task.objects.create_task(
            package_instance=package_instance,
            round_=round_id,
            task_name=task_name,
            points=points,
            judging_mode=judge_mode,
        )
        return {'message': _('Task ') + task_name + _(' created successfully')}

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        return {'message': _('Task creation failed due to invalid data. Please correct the '
                             'following errors:')}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        return {'message': _('Task creation failed due to insufficient permissions.')}

    @classmethod
    def handle_error(cls, request, error: Exception) -> Dict[str, str]:
        return {'message': 'Task creation failed due to the following error:\n' + str(error)}


class CreateTaskFormWidget(FormWidget):
    def __init__(self,
                 request,
                 course_id: int,
                 form: CreateTaskForm = None,
                 **kwargs) -> None:
        from course.views import TaskModelView
        if not form:
            form = CreateTaskForm()

        super().__init__(
            name='create_task_form_widget',
            request=request,
            form=form,
            post_target=TaskModelView.post_url(course_id=course_id),
            button_text=_('Add task'),
            **kwargs
        )


class DeleteTaskForm(BaCa2ModelForm):
    """
    Form for deleting existing :py:class:`course.Task` objects.
    """

    MODEL = Task
    ACTION = Task.BasicAction.DEL

    #: ID of the task to be deleted.
    task_id = forms.IntegerField(
        label=_('Task ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True,
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Deletes the task with the ID provided in the request.

        :param request: POST request containing the task ID.
        :type request: HttpRequest
        :return: Dictionary containing a success message.
        :rtype: Dict[str, str]
        """
        Task.objects.delete_task(int(request.POST.get('task_id')))
        return {'message': _('Task deleted successfully')}

    @classmethod
    def handle_error(cls, request, error) -> Dict[str, str]:
        """
        Returns response message for a request that failed due to an error other than invalid data
        or insufficient permissions.

        :param request: POST request containing the task ID.
        :type request: HttpRequest
        :param error: Error that caused the request to fail.
        :type error: Exception
        :return: Dictionary containing an error message.
        :rtype: Dict[str, str]
        """
        return {'message': 'Task deletion failed due to the following error:\n' + str(error)}

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        """
        Returns response message for a request containing invalid data.

        :param request: POST request containing the task ID.
        :type request: HttpRequest
        :param errors: Dictionary containing information about the errors found in the form data.
        :type errors: dict
        :return: Dictionary containing an error message preceding the list of errors.
        :rtype: Dict[str, str]
        """
        return {'message': _('Task deletion failed due to invalid data. Please correct the '
                             'following errors:')}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        """
        Returns response message for a request from a user without the permission to delete tasks.

        :param request: POST request containing the task ID.
        :type request: HttpRequest
        :return: Dictionary containing an error message.
        :rtype: Dict[str, str]
        """
        return {'message': _('Task deletion failed due to insufficient permissions.')}


class DeleteTaskFormWidget(FormWidget):
    """
    Form widget for deleting tasks.

    See also:
        - :class:`FormWidget`
        - :class:`DeleteTaskForm`
    """

    def __init__(self,
                 request,
                 form: DeleteTaskForm = None,
                 **kwargs) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param form: Form to be base the widget on. If not provided, a new form will be created.
        :type form: :class:`DeleteTaskForm`
        :param kwargs: Additional keyword arguments to be passed to the :class:`FormWidget`
            super constructor.
        :type kwargs: dict
        """
        if not form:
            form = DeleteTaskForm()

        super().__init__(
            name='delete_task_form_widget',
            request=request,
            form=form,
            post_target=ModelFormPostTarget(Task),
            button_text=_('Delete task'),
            submit_confirmation_popup=SubmitConfirmationPopup(
                title=_('Confirm task deletion'),
                message=_(
                    'Are you sure you want to delete this task? This action cannot be undone.'
                ),
                confirm_button_text=_('Delete task'),
            ),
            **kwargs
        )
