import logging
from abc import abstractmethod
from typing import Any, Dict

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.choices import TaskJudgingMode
from core.tools.files import FileHandler
from course.models import Round, Submit, Task
from course.routing import InCourse
from main.models import Course
from util.models_registry import ModelsRegistry
from widgets.forms.base import (
    BaCa2ModelForm,
    CourseModelFormPostTarget,
    FormElementGroup,
    FormWidget,
    ModelFormPostTarget
)
from widgets.forms.fields import (
    AlphanumericStringField,
    ChoiceField,
    DateTimeField,
    FileUploadField,
    ModelChoiceField
)
from widgets.forms.fields.course import CourseName, CourseShortName, USOSCode
from widgets.popups.forms import SubmitConfirmationPopup

logger = logging.getLogger(__name__)


# -------------------------------------- course model form ------------------------------------- #

class CourseModelForm(BaCa2ModelForm):
    """
    Base class for all forms in the BaCa2 app which are used to create, delete or modify course
    database model objects.
    """

    @classmethod
    @abstractmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible and the form data is valid.

        :param request: Request object.
        :type request: HttpRequest
        :return: Dictionary containing a success message and any additional data to be included in
            the response.
        :rtype: Dict[str, Any]
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @classmethod
    def is_permissible(cls, request) -> bool:
        """
        Checks if the user making the request has the permission to perform the action specified by
        the form within the scope of the current course.
        """
        return request.user.has_course_permission(cls.ACTION.label, InCourse.get_context_course())


# =========================================== COURSE =========================================== #

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


# =========================================== MEMBERS ========================================== #

# ----------------------------------------- add members ---------------------------------------- #

class AddMembersForm(BaCa2ModelForm):
    MODEL = Course
    ACTION = Course.CourseAction.ADD_MEMBER

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


# ============================================ ROUND =========================================== #

# ---------------------------------------- create round ---------------------------------------- #

class CreateRoundForm(CourseModelForm):
    MODEL = Round
    ACTION = Round.BasicAction.ADD

    name = AlphanumericStringField(label=_('Round name'), required=True)
    start_date = DateTimeField(label=_('Start date'), required=True)
    end_date = DateTimeField(label=_('End date'), required=False)
    deadline_date = DateTimeField(label=_('Deadline date'), required=True)
    reveal_date = DateTimeField(label=_('Reveal date'), required=False)

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        end_date = request.POST.get('end_date')
        reveal_date = request.POST.get('reveal_date')

        if not end_date:
            end_date = None
        if not reveal_date:
            reveal_date = None

        Round.objects.create_round(
            name=request.POST.get('name'),
            start_date=request.POST.get('start_date'),
            end_date=end_date,
            deadline_date=request.POST.get('deadline_date'),
            reveal_date=reveal_date
        )

        return {'message': _('Round ') + request.POST.get('name') + _(' created successfully')}


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
            element_groups=[
                FormElementGroup(name='start_dates',
                                 elements=['start_date', 'reveal_date'],
                                 layout=FormElementGroup.FormElementsLayout.HORIZONTAL),
                FormElementGroup(name='end_dates',
                                 elements=['end_date', 'deadline_date'],
                                 layout=FormElementGroup.FormElementsLayout.HORIZONTAL)
            ],
            **kwargs
        )


# ----------------------------------------- edit round ----------------------------------------- #

class EditRoundForm(CourseModelForm):
    MODEL = Round
    ACTION = Round.BasicAction.EDIT

    name = AlphanumericStringField(label=_('Round name'), required=True)
    start_date = DateTimeField(label=_('Start date'), required=True)
    end_date = DateTimeField(label=_('End date'), required=False)
    deadline_date = DateTimeField(label=_('Deadline date'), required=True)
    reveal_date = DateTimeField(label=_('Reveal date'), required=False)
    round_id = forms.IntegerField(widget=forms.HiddenInput())

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        round_ = ModelsRegistry.get_round(int(request.POST.get('round_id')))

        round_.update(
            name=request.POST.get('name'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            deadline_date=request.POST.get('deadline_date'),
            reveal_date=request.POST.get('reveal_date'),
        )

        return {'message': _('Round ') + request.POST.get('name') + _(' edited successfully')}


class EditRoundFormWidget(FormWidget):
    def __init__(self,
                 request,
                 course_id: int,
                 round_: int | Round,
                 form: CreateRoundForm = None,
                 **kwargs) -> None:
        from course.views import RoundModelView

        if not form:
            form = EditRoundForm()

        round_obj = ModelsRegistry.get_round(round_, course_id)

        form.fields['name'].initial = round_obj.name
        form.fields['start_date'].initial = round_obj.start_date
        form.fields['end_date'].initial = round_obj.end_date
        form.fields['deadline_date'].initial = round_obj.deadline_date
        form.fields['reveal_date'].initial = round_obj.reveal_date
        form.fields['round_id'].initial = round_obj.pk

        super().__init__(
            name=f'edit_round{round_obj.pk}_form_widget',
            request=request,
            form=form,
            post_target=RoundModelView.post_url(course_id=course_id),
            button_text=f"{_('Edit round')} {round_obj.name}",
            **kwargs
        )


# ---------------------------------------- delete round ---------------------------------------- #

class DeleteRoundForm(BaCa2ModelForm):
    MODEL = Round
    ACTION = Round.BasicAction.DEL

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        pass


# ============================================ TASK ============================================ #

# ----------------------------------------- create task ---------------------------------------- #

class CreateTaskForm(BaCa2ModelForm):
    MODEL = Task
    ACTION = Task.BasicAction.ADD

    task_name = AlphanumericStringField(
        label=_('Task name'),
        help_text=_('If not provided - task name will be taken from package.'),
        required=False,
    )
    round_ = ModelChoiceField(
        data_source_url='',
        label_format_string='[[name]] ([[f_start_date]] - [[f_deadline_date]])',
        label=_('Round'),
        required=True,
    )
    points = forms.FloatField(label=_('Points'),
                              min_value=0,
                              required=False,
                              help_text=_('If not provided - points will be taken from package.'), )
    package = FileUploadField(label=_('Task package'),
                              allowed_extensions=['zip'],
                              required=True,
                              help_text=_('Only .zip files are allowed'))
    judge_mode = ChoiceField(label=_('Judge mode'),
                             choices=TaskJudgingMode,
                             required=True,
                             placeholder_default_option=False)

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
        round_id = int(request.POST.get('round_'))
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
                creator=request.user,
                return_package_instance=True
            )
            Task.objects.create_task(
                package_instance=package_instance,
                round_=round_id,
                task_name=task_name,
                points=points,
                judging_mode=judge_mode,
            )
        except Exception as e:
            file.delete()
            raise e
        file.delete()
        return {'message': _('Task ') + task_name + _(' created successfully')}


class CreateTaskFormWidget(FormWidget):
    def __init__(self,
                 request,
                 course_id: int,
                 form: CreateTaskForm = None,
                 **kwargs) -> None:
        from course.views import RoundModelView, TaskModelView
        if not form:
            form = CreateTaskForm()

        form.fields['round_'].data_source_url = RoundModelView.get_url(
            serialize_kwargs={'add_formatted_dates': True},
            course_id=course_id
        )

        super().__init__(
            name='create_task_form_widget',
            request=request,
            form=form,
            post_target=TaskModelView.post_url(course_id=course_id),
            button_text=_('Add task'),
            element_groups=FormElementGroup(name='grading',
                                            elements=['points', 'judge_mode'],
                                            layout=FormElementGroup.FormElementsLayout.HORIZONTAL),
            **kwargs
        )


# ----------------------------------------- delete task ---------------------------------------- #


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


# ========================================= SUBMISSION ========================================= #

# -------------------------------------- create submission ------------------------------------- #

class CreateSubmitForm(BaCa2ModelForm):
    MODEL = Submit
    ACTION = Submit.BasicAction.ADD

    source_code = FileUploadField(label=_('Source code'), required=True)
    task_id = forms.IntegerField(label=_('Task ID'), widget=forms.HiddenInput(), required=True)

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        file_extension = request.FILES['source_code'].name.split('.')[-1]
        source_code_file = FileHandler(settings.SUBMITS_DIR,
                                       file_extension,
                                       request.FILES['source_code'])
        source_code_file.save()
        task_id = int(request.POST.get('task_id'))
        user = request.user

        try:
            Submit.objects.create_submit(
                source_code=source_code_file.path,
                task=task_id,
                user=user,
                auto_send=False
            )
        except Exception as e:
            source_code_file.delete()
            raise e
        return {'message': _('Submit created successfully')}


class CreateSubmitFormWidget(FormWidget):
    def __init__(self,
                 request,
                 course_id: int,
                 task_id: int,
                 form: CreateTaskForm = None,
                 **kwargs) -> None:
        from course.views import SubmitModelView
        if not form:
            form = CreateSubmitForm()

        form.fields['task_id'].initial = task_id

        super().__init__(
            name='create_submit_form_widget',
            request=request,
            form=form,
            post_target=SubmitModelView.post_url(course_id=course_id),
            button_text=_('New submission'),
            **kwargs
        )
