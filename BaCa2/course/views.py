import inspect
from abc import ABC, ABCMeta
from typing import Any, Callable, Dict, List, Union

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.choices import EMPTY_FINAL_STATUSES, BasicModelAction, ResultStatus, SubmitType
from course.models import Result, Round, Submit, Task
from course.routing import InCourse
from main.models import Course, User
from main.views import CourseModelView as CourseModelManagerView
from main.views import RoleModelView, UserModelView
from util.models_registry import ModelsRegistry
from util.responses import BaCa2JsonResponse
from util.views import BaCa2LoggedInView, BaCa2ModelView
from widgets.attachment import Attachment
from widgets.brief_result_summary import BriefResultSummary
from widgets.code_block import CodeBlock
from widgets.forms.course import (
    AddMemberFormWidget,
    AddMembersFromCSVFormWidget,
    AddRoleFormWidget,
    CreateRoundForm,
    CreateRoundFormWidget,
    CreateSubmitForm,
    CreateSubmitFormWidget,
    CreateTaskForm,
    CreateTaskFormWidget,
    DeleteRoleForm,
    DeleteRoundForm,
    DeleteTaskForm,
    EditRoundForm,
    EditRoundFormWidget,
    EditTaskForm,
    EditTaskFormWidget,
    RejudgeSubmitForm,
    RejudgeTaskForm,
    RejudgeTaskFormWidget,
    RemoveMembersFormWidget,
    ReuploadTaskForm,
    ReuploadTaskFormWidget,
    SimpleEditTaskForm,
    SimpleEditTaskFormWidget
)
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.col_defs import RejudgeSubmitColumn
from widgets.listing.columns import DatetimeColumn, FormSubmitColumn, TextColumn
from widgets.navigation import SideNav
from widgets.text_display import TextDisplayer

# ----------------------------------- Course views abstraction ---------------------------------- #

class ReadCourseViewMeta(ABCMeta):
    """
    Metaclass providing automated database routing for all course Views
    """

    DECORATOR_OFF = ['MODEL']

    def __new__(cls, name, bases, dct):
        """
        Creates new class with the same name, base and dictionary, but wraps all non-static,
        non-class methods and properties with :py:meth`read_course_decorator`

        *Special method signature from* ``django.db.models.base.ModelBase``
        """
        new_class = super().__new__(cls, name, bases, dct)

        for base in bases:
            new_class = cls.decorate_class(result_class=new_class,
                                           attr_donor=base,
                                           decorator=cls.read_course_decorator)
        new_class = cls.decorate_class(result_class=new_class,
                                       attr_donor=dct,
                                       decorator=cls.read_course_decorator)
        return new_class

    @staticmethod
    def decorate_class(result_class,
                       attr_donor: type | dict,
                       decorator: Callable[[Callable, bool], Union[Callable, property]]) -> type:
        """
        Decorates all non-static, non-class methods and properties of donor class with decorator
        and adds them to result class.

        :param result_class: Class to which decorated methods will be added
        :type result_class: type
        :param attr_donor: Class from which methods will be taken, or dictionary of methods
        :type attr_donor: type | dict
        :param decorator: Decorator to be applied to methods
        :type decorator: Callable[[Callable, bool], Union[Callable, property]]

        :returns: Result class with decorated methods
        :rtype: type

        """
        if isinstance(attr_donor, type):
            attr_donor = attr_donor.__dict__
        # Decorate all non-static, non-class methods with the hook method
        for attr_name, attr_value in attr_donor.items():
            if all(((callable(attr_value) or isinstance(attr_value, property)),
                    not attr_name.startswith('_'),
                    not isinstance(attr_value, classmethod),
                    not isinstance(attr_value, staticmethod),
                    not inspect.isclass(attr_value),
                    attr_name not in ReadCourseViewMeta.DECORATOR_OFF)):
                decorated_meth = decorator(attr_value,
                                           isinstance(attr_value, property))
                decorated_meth.__doc__ = attr_value.__doc__
                setattr(result_class,
                        attr_name,
                        decorated_meth)
        return result_class

    @staticmethod
    def read_course_decorator(original_method, prop: bool = False):
        """
        Decorator used to decode origin database from object. It wraps every operation inside
        the object to be performed on meta-read database.

        :param original_method: Original method to be wrapped
        :param prop: Indicates if original method is a property.
        :type prop: bool

        :returns: Wrapped method
        """

        def wrapper_method(self, *args, **kwargs):
            if InCourse.is_defined():
                result = original_method(self, *args, **kwargs)
            else:
                course_id = self.kwargs.get('course_id')
                if not course_id:
                    raise CourseModelView.MissingCourseId('Course not defined in URL params')
                with InCourse(course_id):
                    result = original_method(self, *args, **kwargs)
            return result

        def wrapper_property(self):
            if InCourse.is_defined():
                result = original_method.fget(self)
            else:
                course_id = self.kwargs.get('course_id')
                if not course_id:
                    raise CourseModelView.MissingCourseId('Course not defined in URL params')
                with InCourse(course_id):
                    result = original_method.fget(self)
            return result

        if prop:
            return property(wrapper_property)
        return wrapper_method


class CourseModelView(BaCa2ModelView, ABC, metaclass=ReadCourseViewMeta):
    """
    Base class for all views used to manage course db models and retrieve their data from the
    front-end. GET requests directed at this view are used to retrieve serialized model data
    while POST requests are handled in accordance with the particular course model form from which
    they originate.

    See also:
        - :py:class:`BaCa2ModelView`
        - :py:class:`ReadCourseViewMeta`
    """

    class MissingCourseId(Exception):
        """
        Raised when an attempt is made to construct a course model view URL without a course id.
        """
        pass

    @classmethod
    def _url(cls, **kwargs) -> str:
        """
        :param kwargs: Keyword arguments to be used to construct the URL. Should contain a
            `course_id` parameter.
        :type kwargs: dict
        :return: URL to the view
        :rtype: str
        """
        course_id = kwargs.get('course_id')
        if not course_id:
            raise cls.MissingCourseId('Course id required to construct URL')

        return f'/course/{course_id}/models/{cls.MODEL._meta.model_name}/'

    def check_get_all_permission(self, request, serialize_kwargs, **kwargs) -> bool:
        """
        :param request: HTTP GET request object received by the view
        :type request: HttpRequest
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :return: `True` if the user has permission to view all instances of the model assigned to
            them in the course, `False` otherwise
        :rtype: bool
        """
        user = getattr(request, 'user')
        course_id = self.kwargs.get('course_id')
        return user.has_basic_course_model_permissions(model=self.MODEL,
                                                       course=course_id,
                                                       permissions=BasicModelAction.VIEW)


# ----------------------------------------- Model views ----------------------------------------- #

class RoundModelView(CourseModelView):
    """
    View used to retrieve serialized round model data to be displayed in the front-end and to
    interface between POST requests and course model forms used to manage round instances.
    """

    MODEL = Round

    def post(self, request, **kwargs) -> BaCa2JsonResponse:
        """
        Delegates the handling of the POST request to the appropriate form based on the `form_name`
        parameter received in the request.

        :param request: HTTP POST request object received by the view
        :type request: HttpRequest
        :return: JSON response to the POST request containing information about the success or
            failure of the request
        :rtype: :py:class:`BaCa2JsonResponse`
        """
        form_name = request.POST.get('form_name')

        if form_name == f'{Course.CourseAction.ADD_ROUND.label}_form':
            return CreateRoundForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.EDIT_ROUND.label}_form':
            return EditRoundForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.DEL_ROUND.label}_form':
            return DeleteRoundForm.handle_post_request(request)

        return self.handle_unknown_form(request, **kwargs)


class TaskModelView(CourseModelView):
    """
    View used to retrieve serialized task model data to be displayed in the front-end and to
    interface between POST requests and course model forms used to manage task instances.
    """

    MODEL = Task

    def post(self, request, **kwargs) -> JsonResponse:
        """
        Delegates the handling of the POST request to the appropriate form based on the `form_name`
        parameter received in the request.

        :param request: HTTP POST request object received by the view
        :type request: HttpRequest
        :return: JSON response to the POST request containing information about the success or
            failure of the request
        :rtype: :py:class:`JsonResponse`
        """
        form_name = request.POST.get('form_name')

        if form_name == f'{Course.CourseAction.ADD_TASK.label}_form':
            return CreateTaskForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.REUPLOAD_TASK.label}_form':
            return ReuploadTaskForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.EDIT_TASK.label}_form':
            return SimpleEditTaskForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.DEL_TASK.label}_form':
            return DeleteTaskForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.REJUDGE_TASK.label}_form':
            return RejudgeTaskForm.handle_post_request(request)

        return self.handle_unknown_form(request, **kwargs)


class SubmitModelView(CourseModelView):
    """
    View used to retrieve serialized submit model data to be displayed in the front-end and to
    interface between POST requests and course model forms used to manage submit instances.
    """

    MODEL = Submit

    def post(self, request, **kwargs) -> JsonResponse:
        """
        Delegates the handling of the POST request to the appropriate form based on the `form_name`
        parameter received in the request.

        :param request: HTTP POST request object received by the view
        :type request: HttpRequest
        :return: JSON response to the POST request containing information about the success or
            failure of the request
        :rtype: :py:class:`JsonResponse`
        """
        form_name = request.POST.get('form_name')

        if form_name == f'{Course.CourseAction.ADD_SUBMIT.label}_form':
            return CreateSubmitForm.handle_post_request(request)
        if form_name == f'{Course.CourseAction.REJUDGE_SUBMIT.label}_form':
            return RejudgeSubmitForm.handle_post_request(request)

        return self.handle_unknown_form(request, **kwargs)

    def check_get_filtered_permission(self,
                                      filter_params: dict,
                                      exclude_params: dict,
                                      serialize_kwargs: dict,
                                      query_result: List[Submit],
                                      request,
                                      **kwargs) -> bool:
        """
        :param filter_params: Parameters used to filter the query result
        :type filter_params: dict
        :param exclude_params: Parameters used to exclude the query result
        :type exclude_params: dict
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :param query_result: Query result retrieved by the view
        :type query_result: List[:class:`Submit`]
        :param request: HTTP GET request object received by the view
        :type request: HttpRequest
        :return: `True` if the user has the view_own_submit permission and all the retrieved
            submit instances are owned by the user, `False` otherwise
        :rtype: bool
        """
        user = getattr(request, 'user')
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))

        if not user.has_course_permission(Course.CourseAction.VIEW_OWN_SUBMIT.label, course):
            return False

        return all(submit.usr == user.pk for submit in query_result)


class ResultModelView(CourseModelView):
    """
    View used to retrieve serialized result model data to be displayed in the front-end and to
    interface between POST requests and course model forms used to manage result instances.
    """

    MODEL = Result

    def check_get_all_permission(self, request, serialize_kwargs, **kwargs) -> bool:
        """
        :param request: HTTP GET request object received by the view
        :type request: HttpRequest
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :return: Checks if the user has permission to view all results in the course. If
            `serialize_kwargs` contains `include_time` and/or `include_memory` set to `True`, the
            user also needs to have the view_used_time and/or view_used_memory permissions in the
            course.
        """
        user = getattr(request, 'user')
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))

        if not user.has_course_permission(Course.CourseAction.VIEW_RESULT.label, course):
            return False

        if serialize_kwargs.get('include_time') and not user.has_course_permission(
            Course.CourseAction.VIEW_USED_TIME.label, course
        ):
            return False

        if serialize_kwargs.get('include_memory') and not user.has_course_permission(
            Course.CourseAction.VIEW_USED_MEMORY.label, course
        ):
            return False

        return True

    def check_get_filtered_permission(self,
                                      filter_params: dict,
                                      exclude_params: dict,
                                      serialize_kwargs: dict,
                                      query_result: List[Result],
                                      request,
                                      **kwargs) -> bool:
        """
        :param filter_params: Parameters used to filter the query result
        :type filter_params: dict
        :param exclude_params: Parameters used to exclude the query result
        :type exclude_params: dict
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :param query_result: Query result retrieved by the view
        :type query_result: List[:class:`Result`]
        :param request: HTTP GET request object received by the view
        :type request: HttpRequest
        :return: `True` if the user has the view_own_result permission and all the retrieved
            result instances are owned by the user. If `serialize_kwargs` contains
            `include_time` and/or `include_memory` set to `True`, the user also needs to have
            the view_used_time and/or view_used_memory permissions in the course.
        :rtype: bool
        """
        user = getattr(request, 'user')
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))

        if not user.has_course_permission(Course.CourseAction.VIEW_OWN_RESULT.label, course):
            return False

        if not all(result.submit.usr == user.pk for result in query_result):
            return False

        if serialize_kwargs.get('include_time') and not user.has_course_permission(
            Course.CourseAction.VIEW_USED_TIME.label, course
        ):
            return False

        if serialize_kwargs.get('include_memory') and not user.has_course_permission(
            Course.CourseAction.VIEW_USED_MEMORY.label, course
        ):
            return False

        return True


# ------------------------------------- course member mixin ------------------------------------ #

class CourseMemberMixin(UserPassesTestMixin):
    """
    Mixin for views which require the user to be a member of a specific course referenced in the
    URL of the view being accessed (as a `course_id` parameter). The mixin also allows superusers
    to access the view.

    The mixin also allows for a specific role to be required for the user to access the view If the
    `REQUIRED_ROLE` class attribute is set.
    """

    #: The required role for the user to access the view. If `None`, the user only needs to be a
    #: member of the course. If not `None`, the user needs to have the specified role in the course.
    #: Should be a string with the name of the role.
    REQUIRED_ROLE = None

    def test_func(self) -> bool:
        """
        :return: `True` if the user is a member of the course or a superuser, `False` otherwise. If
            the `REQUIRED_ROLE` attribute is set, non-superusers also need to have the specified
            role in the course to pass the test.
        :rtype: bool
        """
        kwargs = getattr(self, 'kwargs')
        request = getattr(self, 'request')

        if not kwargs or not request:
            raise TypeError('CourseMemberMixin requires "kwargs" and "request" attrs to be set')

        course_id = kwargs.get('course_id')

        if not course_id:
            raise TypeError('CourseMemberMixin should only be used with views that have a '
                            '"course_id" parameter in their URL')

        course = ModelsRegistry.get_course(course_id)

        if request.user.is_superuser:
            return True
        if not self.REQUIRED_ROLE:
            return course.user_is_member(request.user)
        if self.REQUIRED_ROLE == 'admin':
            return course.user_is_admin(request.user)

        return course.user_has_role(request.user, self.REQUIRED_ROLE)


class CourseTemplateView(BaCa2LoggedInView, CourseMemberMixin):
    def get(self, request, *args, **kwargs) -> TemplateResponse:
        course_id = kwargs.get('course_id')
        self.request.course_id = course_id
        return super().get(request, *args, **kwargs)


# ----------------------------------------- User views ----------------------------------------- #

class CourseView(CourseTemplateView):
    template_name = 'course_admin.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        user = getattr(self.request, 'user')
        course_id = self.kwargs.get('course_id')
        course = ModelsRegistry.get_course(course_id)
        context['page_title'] = course.name
        sidenav_tabs = ['Members', 'Roles', 'Rounds', 'Tasks', 'Results']
        sidenav_sub_tabs = {tab: [] for tab in sidenav_tabs}

        # members --------------------------------------------------------------------------------

        if user.has_course_permission(Course.CourseAction.VIEW_MEMBER.label, course):
            sidenav_sub_tabs.get('Members').append('View members')
            context['view_members_tab'] = 'view-members-tab'

            members_table = TableWidget(
                name='members_table_widget',
                title=_('Course members'),
                request=self.request,
                data_source=UserModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    filter_params={'roles__course': course_id},
                    serialize_kwargs={'course': course_id},
                ),
                cols=[TextColumn(name='first_name', header=_('First name')),
                      TextColumn(name='last_name', header=_('Last name')),
                      TextColumn(name='email', header=_('Email address')),
                      TextColumn(name='user_role', header=_('Role'))],
                refresh_button=True,
            )
            self.add_widget(context, members_table)

        if user.has_course_permission(Course.CourseAction.ADD_MEMBER.label, course):
            sidenav_sub_tabs.get('Members').append('Add member')
            context['add_member_tab'] = 'add-member-tab'

            add_member_form = AddMemberFormWidget(request=self.request, course_id=course_id)
            self.add_widget(context, add_member_form)

        if user.has_course_permission(Course.CourseAction.ADD_MEMBERS_CSV.label, course):
            sidenav_sub_tabs.get('Members').append('Add members from CSV')
            context['add_members_csv_tab'] = 'add-members-from-csv-tab'

            add_members_csv_form = AddMembersFromCSVFormWidget(request=self.request,
                                                               course_id=course_id)
            self.add_widget(context, add_members_csv_form)

        if user.has_course_permission(Course.CourseAction.DEL_MEMBER.label, course):
            sidenav_sub_tabs.get('Members').append('Remove members')
            context['remove_members_tab'] = 'remove-members-tab'

            remove_members_form = RemoveMembersFormWidget(request=self.request, course_id=course_id)
            self.add_widget(context, remove_members_form)

        # roles ----------------------------------------------------------------------------------

        if user.has_course_permission(Course.CourseAction.VIEW_ROLE.label, course):
            sidenav_sub_tabs.get('Roles').append('View roles')
            context['view_roles_tab'] = 'view-roles-tab'

            roles_table_kwargs = {
                'name': 'roles_table_widget',
                'title': _('Roles'),
                'request': self.request,
                'data_source': RoleModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    filter_params={'course': course_id},
                ),
                'cols': [TextColumn(name='name', header=_('Role name')),
                         TextColumn(name='description', header=_('Description'))],
                'refresh_button': True,
                'link_format_string': '/main/role/[[id]]/'
            }

            if user.has_course_permission(Course.CourseAction.DEL_ROLE.label, course):
                roles_table_kwargs = roles_table_kwargs | {
                    'allow_select': True,
                    'allow_delete': True,
                    'delete_form': DeleteRoleForm(),
                    'data_post_url': CourseModelManagerView.post_url(**{'course_id': course_id}),
                }

            self.add_widget(context, TableWidget(**roles_table_kwargs))

        if user.has_course_permission(Course.CourseAction.ADD_ROLE.label, course):
            sidenav_sub_tabs.get('Roles').append('Add role')
            context['add_role_tab'] = 'add-role-tab'

            add_role_form = AddRoleFormWidget(request=self.request, course_id=course_id)
            self.add_widget(context, add_role_form)

        # rounds ---------------------------------------------------------------------------------

        if user.has_course_permission(Course.CourseAction.VIEW_ROUND.label, course):
            sidenav_sub_tabs.get('Rounds').append('View rounds')
            context['view_rounds_tab'] = 'view-rounds-tab'

            rounds_table_kwargs = {
                'name': 'rounds_table_widget',
                'title': _('Rounds'),
                'request': self.request,
                'data_source': RoundModelView.get_url(**{'course_id': course_id}),
                'cols': [TextColumn(name='name', header=_('Round name')),
                         DatetimeColumn(name='start_date', header=_('Start date')),
                         DatetimeColumn(name='end_date', header=_('End date')),
                         DatetimeColumn(name='deadline_date', header=_('Deadline date')),
                         DatetimeColumn(name='reveal_date', header=_('Reveal date')),
                         TextColumn(name='score_selection_policy',
                                    header=_('Score selection policy'))],
                'refresh_button': True,
                'default_order_col': 'start_date',
                'default_order_asc': True,
            }

            if user.has_course_permission(Course.CourseAction.EDIT_ROUND.label, course):
                rounds_table_kwargs['link_format_string'] = (f'/course/{course_id}/round-edit/'
                                                             f'?tab=[[normalized_name]]-tab#')

            if user.has_course_permission(Course.CourseAction.DEL_ROUND.label, course):
                rounds_table_kwargs = rounds_table_kwargs | {
                    'allow_select': True,
                    'allow_delete': True,
                    'delete_form': DeleteRoundForm(),
                    'data_post_url': RoundModelView.post_url(**{'course_id': course_id}),
                }

            self.add_widget(context, TableWidget(**rounds_table_kwargs))

        if user.has_course_permission(Course.CourseAction.ADD_ROUND.label, course):
            sidenav_sub_tabs.get('Rounds').append('Add round')
            context['add_round_tab'] = 'add-round-tab'

            add_round_form = CreateRoundFormWidget(request=self.request, course_id=course_id)
            self.add_widget(context, add_round_form)

        # tasks ----------------------------------------------------------------------------------

        if user.has_course_permission(Course.CourseAction.VIEW_TASK.label, course):
            sidenav_sub_tabs.get('Tasks').append('View tasks')
            context['view_tasks_tab'] = 'view-tasks-tab'

            tasks_table_kwargs = {
                'name': 'tasks_table_widget',
                'title': _('Tasks'),
                'request': self.request,
                'data_source': TaskModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    exclude_params={'is_legacy': True},
                    serialize_kwargs={'submitter': user, 'add_legacy_submits_amount': True},
                    **{'course_id': course_id}
                ),
                'cols': [TextColumn(name='name', header=_('Task name')),
                         TextColumn(name='round_name', header=_('Round')),
                         TextColumn(name='judging_mode', header=_('Judging mode')),
                         TextColumn(name='points', header=_('Max points')),
                         TextColumn(name='user_formatted_score', header=_('My score'))],
                'refresh_button': True,
                'default_order_col': 'round_name',
                'link_format_string': f'/course/{course_id}/task/[[id]]',
            }

            if user.has_course_permission(Course.CourseAction.DEL_TASK.label, course):
                tasks_table_kwargs = tasks_table_kwargs | {
                    'allow_select': True,
                    'allow_delete': True,
                    'delete_form': DeleteTaskForm(),
                    'data_post_url': TaskModelView.post_url(**{'course_id': course_id}),
                }

            if user.has_course_permission(Course.CourseAction.REJUDGE_TASK.label, course):
                tasks_table_kwargs['cols'] += [
                    FormSubmitColumn(
                        name='rejudge_task',
                        form_widget=RejudgeTaskFormWidget(request=self.request,
                                                          course_id=course_id),
                        mappings={'task_id': 'id'},
                        btn_icon='exclamation-triangle',
                        btn_text='[[legacy_submits_amount]]',
                        header_icon='clock-history',
                        condition_key='has_legacy_submits',
                        condition_value='true',
                        disabled_appearance=FormSubmitColumn.DisabledAppearance.ICON,
                        disabled_content='check-lg'
                    )
                ]

            self.add_widget(context, TableWidget(**tasks_table_kwargs))

        if user.has_course_permission(Course.CourseAction.ADD_TASK.label, course):
            sidenav_sub_tabs.get('Tasks').append('Add task')
            context['add_task_tab'] = 'add-task-tab'

            add_task_form = CreateTaskFormWidget(request=self.request, course_id=course_id)
            self.add_widget(context, add_task_form)

        # results --------------------------------------------------------------------------------

        view_all_submits = user.has_course_permission(Course.CourseAction.VIEW_SUBMIT.label,
                                                      course)
        view_own_submits = user.has_course_permission(Course.CourseAction.VIEW_OWN_SUBMIT.label,
                                                      course)
        view_all_results = user.has_course_permission(Course.CourseAction.VIEW_RESULT.label,
                                                      course)
        view_own_results = user.has_course_permission(Course.CourseAction.VIEW_OWN_RESULT.label,
                                                      course)

        if view_all_submits or view_own_submits:
            sidenav_sub_tabs.get('Results').append('View results')
            context['results_tab'] = 'results-tab'

            results_table_kwargs = {
                'name': 'results_table_widget',
                'title': _('Results'),
                'request': self.request,
                'cols': [TextColumn(name='task_name', header=_('Task name')),
                         DatetimeColumn(name='submit_date', header=_('Submit time')),
                         TextColumn(name='submit_status', header=_('Submit status')),
                         TextColumn(name='summary_score', header=_('Score'))],
                'refresh_button': True,
                'paging': TableWidgetPaging(page_length=50,
                                            allow_length_change=True,
                                            length_change_options=[10, 25, 50, 100]),
                'default_order_col': 'submit_date',
                'default_order_asc': False,
            }

            if view_all_submits:
                results_table_kwargs['data_source'] = SubmitModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    exclude_params={'submit_type': SubmitType.HID},
                    serialize_kwargs={'add_round_task_name': True,
                                      'add_summary_score': True, },
                    course_id=course_id
                )
                results_table_kwargs['cols'].extend([
                    TextColumn(name='user_first_name', header=_('Submitter first name')),
                    TextColumn(name='user_last_name', header=_('Submitter last name'))
                ])
            else:
                results_table_kwargs['data_source'] = SubmitModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    filter_params={'usr': user.id,
                                   'submit_type': SubmitType.STD},
                    serialize_kwargs={'add_round_task_name': True,
                                      'add_summary_score': True,
                                      'add_falloff_info': True, },
                    course_id=course_id
                )
                results_table_kwargs['cols'].extend([
                    TextColumn(name='fall_off_factor', header='Fall-off factor')
                ])

            if user.has_course_permission(Course.CourseAction.REJUDGE_SUBMIT.label, course):
                results_table_kwargs['cols'].append(RejudgeSubmitColumn(
                    course_id=course_id,
                    request=self.request
                ))

            if view_all_results or view_own_results:
                results_table_kwargs['link_format_string'] = f'/course/{course_id}/submit/[[id]]/'

            self.add_widget(context, TableWidget(**results_table_kwargs))

        # side nav -------------------------------------------------------------------------------

        sidenav_tabs = [tab for tab in sidenav_tabs if sidenav_sub_tabs.get(tab)]
        sidenav_sub_tabs = {tab: sub_tabs for tab, sub_tabs in sidenav_sub_tabs.items()
                            if len(sub_tabs) > 1}

        if len(sidenav_sub_tabs) > 1:
            toggle_button = True
        else:
            toggle_button = False

        sidenav = SideNav(request=self.request,
                          collapsed=False,
                          toggle_button=toggle_button,
                          tabs=sidenav_tabs,
                          sub_tabs=sidenav_sub_tabs)
        self.add_widget(context, sidenav)

        if context.get('view_members_tab') and 'Members' not in sidenav_sub_tabs:
            context['view_members_tab'] = 'members-tab'
        if context.get('add_members_tab') and 'Members' not in sidenav_sub_tabs:
            context['add_members_tab'] = 'members-tab'
        if context.get('remove_members_tab') and 'Members' not in sidenav_sub_tabs:
            context['remove_members_tab'] = 'members-tab'

        if context.get('view_roles_tab') and 'Roles' not in sidenav_sub_tabs:
            context['view_roles_tab'] = 'roles-tab'
        if context.get('add_role_tab') and 'Roles' not in sidenav_sub_tabs:
            context['add_role_tab'] = 'roles-tab'

        if context.get('view_rounds_tab') and 'Rounds' not in sidenav_sub_tabs:
            context['view_rounds_tab'] = 'rounds-tab'
        if context.get('add_round_tab') and 'Rounds' not in sidenav_sub_tabs:
            context['add_round_tab'] = 'rounds-tab'

        if context.get('view_tasks_tab') and 'Tasks' not in sidenav_sub_tabs:
            context['view_tasks_tab'] = 'tasks-tab'
        if context.get('add_task_tab') and 'Tasks' not in sidenav_sub_tabs:
            context['add_task_tab'] = 'tasks-tab'

        return context


class CourseTask(CourseTemplateView):
    template_name = 'course_task.html'

    def test_func(self) -> bool:
        if not super().test_func():
            return False

        user = getattr(self.request, 'user')
        course_id = self.kwargs.get('course_id')

        return user.has_course_permission(Course.CourseAction.VIEW_TASK.label, course_id)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        user = getattr(self.request, 'user')
        course_id = self.kwargs.get('course_id')
        course = ModelsRegistry.get_course(course_id)
        task_id = self.kwargs.get('task_id')
        task = ModelsRegistry.get_task(task_id, course_id)
        context['page_title'] = task.task_name
        sidenav_tabs = ['Description']

        # description ----------------------------------------------------------------------------
        package = task.package_instance.package

        description_extension = package.doc_extension()
        description_file = package.doc_path(description_extension)
        kwargs = {}

        if package.doc_has_extension('pdf'):
            pdf_path = task.package_instance.pdf_docs_path

            if description_extension == 'pdf':
                description_file = pdf_path
            else:
                kwargs['pdf_download'] = pdf_path

        description_displayer = TextDisplayer(name='description',
                                              file_path=description_file,
                                              download_name=f'{task.task_name}.pdf',
                                              **kwargs)
        self.add_widget(context, description_displayer)

        attachments_static = task.package_instance.attachments
        attachments = []
        cnt = 0
        for attachment in attachments_static:
            attachments.append(Attachment(
                name=f'attachment_{cnt}',
                title=attachment.name,
                link=attachment.path,
                download_name=attachment.name
            ))
            cnt += 1
        context['attachments'] = attachments

        # edit task ------------------------------------------------------------------------------
        can_reupload = user.has_course_permission(Course.CourseAction.REUPLOAD_TASK.label, course)
        can_edit = user.has_course_permission(Course.CourseAction.EDIT_TASK.label, course)

        if can_edit:
            simple_edit_task_form = SimpleEditTaskFormWidget(
                request=self.request,
                course_id=course_id,
                task_id=task_id,
            )
            self.add_widget(context, simple_edit_task_form)
            sidenav_tabs.append('Edit')
            context['edit_tab'] = 'edit-tab'
        if can_reupload:
            reupload_package_form = ReuploadTaskFormWidget(
                request=self.request,
                course_id=course_id,
                task_id=task_id,
            )
            self.add_widget(context, reupload_package_form)
            sidenav_tabs.append('Reupload')
            context['reupload_tab'] = 'reupload-tab'

        # submit form ----------------------------------------------------------------------------

        if task.can_submit(user):
            sidenav_tabs.append('Submit')
            context['submit_tab'] = 'submit-tab'
            submit_form = CreateSubmitFormWidget(request=self.request,
                                                 course_id=course_id,
                                                 task_id=task_id)
            self.add_widget(context, submit_form)

        # results list ---------------------------------------------------------------------------

        view_all_submits = user.has_course_permission(Course.CourseAction.VIEW_SUBMIT.label,
                                                      course)
        view_own_submits = user.has_course_permission(Course.CourseAction.VIEW_OWN_SUBMIT.label,
                                                      course)
        view_all_results = user.has_course_permission(Course.CourseAction.VIEW_RESULT.label,
                                                      course)
        view_own_results = user.has_course_permission(Course.CourseAction.VIEW_OWN_RESULT.label,
                                                      course)

        if view_all_submits or view_own_submits:
            sidenav_tabs.append('Results')
            context['results_tab'] = 'results-tab'

            results_table_kwargs = {
                'name': 'results_table_widget',
                'title': _('Results'),
                'request': self.request,
                'cols': [DatetimeColumn(name='submit_date', header=_('Submit time')),
                         TextColumn(name='submit_status', header=_('Submit status')),
                         TextColumn(name='summary_score', header=_('Score')),
                         TextColumn(name='fall_off_factor', header='Fall-off factor')],
                'refresh_button': True,
                'paging': TableWidgetPaging(page_length=50,
                                            allow_length_change=True,
                                            length_change_options=[10, 25, 50, 100]),
                'default_order_col': 'submit_date',
                'default_order_asc': False,
            }

            if view_all_submits:
                results_table_kwargs['data_source'] = SubmitModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    filter_params={'task': task_id},
                    serialize_kwargs={'add_round_task_name': True,
                                      'add_summary_score': True,
                                      'add_falloff_info': True},
                    course_id=course_id
                )
                results_table_kwargs['cols'].insert(0, TextColumn(name='user_first_name',
                                                                  header=_('Name')))
                results_table_kwargs['cols'].insert(1, TextColumn(name='user_last_name',
                                                                  header=_('Surname')))

            else:
                results_table_kwargs['data_source'] = SubmitModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    filter_params={'usr': user.id,
                                   'submit_type': SubmitType.STD,
                                   'task': task_id},
                    serialize_kwargs={'add_round_task_name': True,
                                      'add_summary_score': True,
                                      'add_falloff_info': True},
                    course_id=course_id
                )

            if view_all_results or view_own_results:
                results_table_kwargs['link_format_string'] = f'/course/{course_id}/submit/[[id]]/'

            if user.has_course_permission(Course.CourseAction.REJUDGE_SUBMIT.label, course):
                results_table_kwargs['cols'].append(RejudgeSubmitColumn(
                    course_id=course_id,
                    request=self.request
                ))

            self.add_widget(context, TableWidget(**results_table_kwargs))

        # side nav -------------------------------------------------------------------------------

        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=sidenav_tabs)
        self.add_widget(context, sidenav)

        return context


class TaskEditView(CourseTemplateView):
    template_name = 'task_edit.html'

    def test_func(self) -> bool:
        if not super().test_func():
            return False

        user = getattr(self.request, 'user')
        course_id = self.kwargs.get('course_id')

        return user.has_course_permission(Course.CourseAction.EDIT_TASK.label, course_id)

    def get_sidenav(self, task_form: EditTaskForm) -> SideNav:
        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=['General settings'], )
        for test_set in task_form.set_groups:
            sidenav.add_tab(
                tab_name=test_set['name'],
                sub_tabs=[f'{test_set["name"]} settings'] + [
                    test_set_test['name']
                    for test_set_test in
                    test_set['test_groups']
                ]
            )
        return sidenav

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        task_id = self.kwargs.get('task_id')
        task = ModelsRegistry.get_task(task_id, course_id)
        context['page_title'] = task.task_name + _(' - edit')
        task_form = EditTaskFormWidget(request=self.request, course_id=course_id, task_id=task_id)
        self.add_widget(context, task_form)
        self.add_widget(context, task_form.get_sidenav(self.request))

        return context


class RoundEditView(CourseTemplateView):
    template_name = 'course_edit_round.html'
    REQUIRED_ROLE = 'admin'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        course_id = self.kwargs.get('course_id')
        course = ModelsRegistry.get_course(course_id)
        context['page_title'] = course.name + _(' - rounds')
        rounds = course.rounds()
        rounds = sorted(rounds, key=lambda x: x.name)
        round_names = [r.name for r in rounds]
        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=round_names, )
        self.add_widget(context, sidenav)

        rounds_context = []
        form_instance_id = 0

        for r in rounds:
            round_edit_form = EditRoundFormWidget(
                request=self.request,
                course_id=course_id,
                round_=r,
                form_instance_id=form_instance_id,
            )
            rounds_context.append({
                'tab_name': SideNav.normalize_tab_name(r.name),
                'round_name': r.name,
                'round_edit_form': round_edit_form,
            })
            form_instance_id += 1

        context['rounds'] = rounds_context

        return context


class SubmitSummaryView(CourseTemplateView):
    template_name = 'course_submit_summary.html'

    @staticmethod
    def _display_test_summaries(user: User, course: Course) -> bool:
        return any([
            user.has_course_permission(Course.CourseAction.VIEW_COMPILE_LOG.label, course),
            user.has_course_permission(Course.CourseAction.VIEW_CHECKER_LOG.label, course),
            user.has_course_permission(Course.CourseAction.VIEW_STUDENT_OUTPUT.label, course),
            user.has_course_permission(Course.CourseAction.VIEW_BENCHMARK_OUTPUT.label, course),
        ])

    def test_func(self) -> bool:
        if not super().test_func():
            return False

        course_id = self.kwargs.get('course_id')
        course = ModelsRegistry.get_course(course_id)
        user = getattr(self.request, 'user')

        if user.has_course_permission(Course.CourseAction.VIEW_RESULT.label, course):
            return True

        submit_id = self.kwargs.get('submit_id')
        submit = ModelsRegistry.get_submit(submit_id, course_id)

        if not submit.user == user:
            return False

        return user.has_course_permission(Course.CourseAction.VIEW_OWN_RESULT.label, course)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = getattr(self.request, 'user')
        course_id = self.kwargs.get('course_id')
        submit_id = self.kwargs.get('submit_id')
        submit = ModelsRegistry.get_submit(submit_id, course_id)

        with InCourse(course_id):
            task = submit.task

        course = ModelsRegistry.get_course(course_id)
        context['page_title'] = f'{task.task_name} - submit #{submit.pk}'

        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=['Summary'])

        context['summary_tab'] = 'summary-tab'

        # summary table --------------------------------------------------------------------------

        submit_summary = [
            {'title': _('Course'), 'value': course.name},
            {'title': _('Round'), 'value': task.round_.name},
            {'title': _('Task'), 'value': task.task_name},
            {'title': _('User'), 'value': submit.user.get_full_name()},
            {'title': _('Submit time'),
             'value': submit.submit_date.astimezone(timezone.get_current_timezone()).strftime(
                 '%Y-%m-%d %H:%M:%S')},
            {'title': _('Submit status'), 'value': submit.formatted_submit_status},
        ]
        if submit.submit_status != ResultStatus.PND:
            submit_summary.extend([
                {'title': _('Score'), 'value': submit.summary_score},
                {'title': _('Fall-off factor'),
                 'value': Submit.format_score(submit.fall_off_factor)},
            ])

        summary_table = TableWidget(
            name='summary_table_widget',
            request=self.request,
            cols=[
                TextColumn(name='title', sortable=False),
                TextColumn(name='value', sortable=False)
            ],
            data_source=submit_summary,
            title=_('Summary') + f' - {_("submit")} #{submit.pk}',
            allow_global_search=False,
            hide_col_headers=True,
            default_sorting=False,
        )
        self.add_widget(context, summary_table)

        # solution code --------------------------------------------------------------------------

        if user.has_course_permission(Course.CourseAction.VIEW_CODE.label, course):
            sidenav.add_tab(_('Code'))
            context['code_tab'] = 'code-tab'
            source_code = CodeBlock(
                name='source_code_block',
                title=_('Source code'),
                code=submit.source_code_path,
            )
            self.add_widget(context, source_code)

        # pending status -------------------------------------------------------------------------

        if submit.submit_status in EMPTY_FINAL_STATUSES + [ResultStatus.PND]:
            context['sets'] = []
            self.add_widget(context, sidenav)
            return context

        # sets -----------------------------------------------------------------------------------

        sets = task.sets
        sets = sorted(sets, key=lambda x: x.short_name)
        sets_list = []

        results_to_parse = sorted(submit.results, key=lambda x: x.test_.short_name)
        results = {}

        for res in results_to_parse:
            test_set_id = res.test_.test_set_id
            if test_set_id not in results:
                results[test_set_id] = {}
            results[test_set_id][res.test_id] = res

        view_used_time = user.has_course_permission(Course.CourseAction.VIEW_USED_TIME.label,
                                                    course)
        view_used_memory = user.has_course_permission(Course.CourseAction.VIEW_USED_MEMORY.label,
                                                      course)
        display_test_summaries = self._display_test_summaries(user, course)

        for s in sets:
            set_context = {
                'set_name': s.short_name,
                'set_id': s.pk,
                'tests': [],
            }

            if display_test_summaries:
                sidenav.add_tab(tab_name=s.short_name)

            serialize_kwargs = {'include_time': False, 'include_memory': False}

            if view_used_time:
                serialize_kwargs['include_time'] = True
            if view_used_memory:
                serialize_kwargs['include_memory'] = True

            cols = [
                TextColumn(name='test_name', header=_('Test')),
                TextColumn(name='f_status', header=_('Status')),
            ]

            if view_used_time:
                cols.append(TextColumn(name='f_time_real',
                                       header=_('Time'),
                                       searchable=False))
            if view_used_memory:
                cols.append(TextColumn(name='f_runtime_memory',
                                       header=_('Memory'),
                                       searchable=False))

            set_summary = TableWidget(
                name=f'set_{s.pk}_summary_table_widget',
                request=self.request,
                data_source=ResultModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    filter_params={'submit': submit_id, 'test__test_set_id': s.pk},
                    serialize_kwargs=serialize_kwargs,
                    course_id=course_id,
                ),
                cols=cols,
                title=f'{_("Set")} {s.short_name} - {_("weight:")} {s.weight}',
                default_order_col='test_name',
            )
            set_context['table_widget'] = set_summary.get_context()

            # test results -----------------------------------------------------------------------

            tests = sorted(s.tests, key=lambda x: x.short_name)

            show_compile_log = user.has_course_permission(
                Course.CourseAction.VIEW_COMPILE_LOG.label,
                course
            )
            show_checker_log = user.has_course_permission(
                Course.CourseAction.VIEW_CHECKER_LOG.label,
                course
            )

            for test in tests:
                brief_result_summary = BriefResultSummary(
                    set_name=s.short_name,
                    test_name=test.short_name,
                    result=results[s.pk][test.pk],
                    include_time=view_used_time,
                    include_memory=view_used_memory,
                    show_compile_log=show_compile_log,
                    show_checker_log=show_checker_log,
                )
                set_context['tests'].append(brief_result_summary.get_context())

            sets_list.append(set_context)

        context['display_test_summaries'] = display_test_summaries
        context['sets'] = sets_list

        if len(sidenav.tabs) > 1:
            context['display_sidenav'] = True
            self.add_widget(context, sidenav)

        return context
