import inspect
from abc import ABC, ABCMeta
from typing import Any, Callable, Dict, List, Union

import django.db.models
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from course.models import Result, Round, Submit, Task
from course.routing import InCourse
from main.views import UserModelView
from util.models_registry import ModelsRegistry
from util.views import BaCa2LoggedInView, BaCa2ModelView
from widgets.forms.course import (
    AddMembersFormWidget,
    CreateRoundForm,
    CreateRoundFormWidget,
    CreateSubmitForm,
    CreateSubmitFormWidget,
    CreateTaskForm,
    CreateTaskFormWidget,
    DeleteTaskForm,
    EditRoundForm,
    EditRoundFormWidget
)
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.columns import DatetimeColumn, TextColumn
from widgets.navigation import SideNav
from widgets.text_display import MarkupDisplayer

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
    class MissingCourseId(Exception):
        pass

    @classmethod
    def _url(cls, **kwargs) -> str:
        course_id = kwargs.get('course_id')
        if not course_id:
            raise cls.MissingCourseId('Course id required to construct URL')

        return f'/course/{course_id}/models/{cls.MODEL._meta.model_name}/'


# ----------------------------------------- Model views ----------------------------------------- #

class RoundModelView(CourseModelView):
    MODEL = Round

    def check_get_filtered_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        return True

    def check_get_excluded_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        return True

    def post(self, request, **kwargs) -> JsonResponse:
        if request.POST.get('form_name') == 'add_round_form':
            return CreateRoundForm.handle_post_request(request)
        elif request.POST.get('form_name') == 'change_round_form':
            return EditRoundForm.handle_post_request(request)
        return self.handle_unknown_form(request, **kwargs)


class TaskModelView(CourseModelView):
    MODEL = Task

    def check_get_filtered_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        return True

    def check_get_excluded_permission(self, query_params: dict,
                                      query_result: List[django.db.models.Model], request,
                                      **kwargs) -> bool:
        return True

    def post(self, request, **kwargs) -> JsonResponse:
        if request.POST.get('form_name') == 'add_task_form':
            return CreateTaskForm.handle_post_request(request)
        elif request.POST.get('form_name') == 'delete_task_form':
            return DeleteTaskForm.handle_post_request(request)
        return self.handle_unknown_form(request, **kwargs)


class SubmitModelView(CourseModelView):
    MODEL = Submit

    def check_get_filtered_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        return True

    def check_get_excluded_permission(self, query_params: dict,
                                      query_result: List[django.db.models.Model], request,
                                      **kwargs) -> bool:
        return True

    def post(self, request, **kwargs) -> JsonResponse:
        if request.POST.get('form_name') == 'add_submit_form':
            return CreateSubmitForm.handle_post_request(request)
        return self.handle_unknown_form(request, **kwargs)


class ResultModelView(CourseModelView):
    MODEL = Result

    class MissingSubmitId(Exception):
        pass

    # @classmethod
    # def _url(cls, **kwargs) -> str:
    #     url = super()._url(**kwargs)
    #     submit_id = kwargs.get('submit_id')
    #     if not submit_id:
    #         raise cls.MissingSubmitId('Submit id required to construct URL')
    #     return f'{url}/submit/{submit_id}'

    def check_get_filtered_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        return True

    def check_get_excluded_permission(self, query_params: dict,
                                      query_result: List[django.db.models.Model], request,
                                      **kwargs) -> bool:
        return True

    def post(self, request, **kwargs) -> JsonResponse:
        pass


# ----------------------------------------- User views ----------------------------------------- #

class CourseView(BaCa2LoggedInView):
    """
    View for non-admin members of a course. Only accessible if the user is a member of the course.
    For course admins and superusers, redirects to the course admin page.
    """

    template_name = 'course.html'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """
        Checks if the user is an admin of the course or a superuser. If so, redirects to the course
        admin page. If not, checks if the user is a member of the course. If so, returns the course
        page. If not, returns an HTTP 403 Forbidden error.
        """
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))
        if course.user_is_admin(request.user) or request.user.is_superuser:
            return redirect('course:course-admin', course_id=course.id)
        if not course.user_is_member(request.user):
            return HttpResponseForbidden(_('You are neither a member of this course nor an admin.\n'
                                           'You are not allowed to view this page.'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        sidenav = SideNav(request=self.request,
                          collapsed=False,
                          toggle_button=False,
                          tabs=['My results', 'Tasks', 'Members'])
        self.add_widget(context, sidenav)
        return context


class CourseAdmin(BaCa2LoggedInView, UserPassesTestMixin):
    """
    View for admins of a course. Only accessible if the user is an admin of the course or a
    superuser.
    """

    template_name = 'course_admin.html'

    def test_func(self) -> bool:
        """
        Test function for UserPassesTestMixin.

        :return: `True` if the user is an admin of the course or a superuser, `False` otherwise.
        :rtype: bool
        """
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))
        return course.user_is_admin(self.request.user) or self.request.user.is_superuser

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')

        sidenav = SideNav(request=self.request,
                          collapsed=False,
                          toggle_button=True,
                          tabs=['Members', 'Rounds', 'Tasks', 'Results'],
                          sub_tabs={'Members': ['View members', 'Add members'],
                                    'Rounds': ['View rounds', 'Add round'],
                                    'Tasks': ['View tasks', 'Add task']}, )
        self.add_widget(context, sidenav)

        # members --------------------------------------------------------------
        members_table = TableWidget(
            name='members_table_widget',
            request=self.request,
            data_source=UserModelView.get_url(
                mode=BaCa2ModelView.GetMode.FILTER,
                query_params={'roles__course': course_id},
                serialize_kwargs={'course': course_id},
            ),
            cols=[TextColumn(name='first_name', header=_('First name')),
                  TextColumn(name='last_name', header=_('Last name')),
                  TextColumn(name='email', header=_('Email address')),
                  TextColumn(name='user_role', header=_('Role'))],
            title=_('Course members'),
        )
        self.add_widget(context, members_table)

        add_members_form = AddMembersFormWidget(request=self.request, course_id=course_id)
        self.add_widget(context, add_members_form)

        # rounds ---------------------------------------------------------------
        round_table = TableWidget(
            name='rounds_table_widget',
            request=self.request,
            data_source=RoundModelView.get_url(course_id=course_id),
            cols=[TextColumn(name='name', header=_('Round name')),
                  DatetimeColumn(name='start_date', header=_('Start date')),
                  DatetimeColumn(name='end_date', header=_('End date')),
                  DatetimeColumn(name='deadline_date', header=_('Deadline date')),
                  DatetimeColumn(name='reveal_date', header=_('Reveal date'))],
            title=_('Rounds'),
            refresh_button=True,
            link_format_string=f'/course/{course_id}/round-edit/?tab=[[normalized_name]]-tab#'
        )
        self.add_widget(context, round_table)

        add_round_form = CreateRoundFormWidget(request=self.request, course_id=course_id)
        self.add_widget(context, add_round_form)

        # tasks ----------------------------------------------------------------
        tasks_table = TableWidget(
            name='tasks_table_widget',
            request=self.request,
            data_source=TaskModelView.get_url(course_id=course_id),
            cols=[TextColumn(name='name', header=_('Task name')),
                  TextColumn(name='round_name', header=_('Round')),
                  TextColumn(name='judging_mode', header=_('Judging mode')),
                  TextColumn(name='points', header=_('Max points'))],
            title=_('Tasks'),
            refresh_button=True,
            default_order_col='round_name',
            allow_delete=True,
            delete_form=DeleteTaskForm(),
            data_post_url=TaskModelView.post_url(course_id=course_id),
            link_format_string=f'/course/{course_id}/task/[[id]]',
        )
        self.add_widget(context, tasks_table)

        add_task_form = CreateTaskFormWidget(request=self.request, course_id=course_id)
        self.add_widget(context, add_task_form)

        results_table = TableWidget(
            name='results_table_widget',
            request=self.request,
            data_source=SubmitModelView.get_url(
                serialize_kwargs={'add_round_task_name': True,
                                  'add_summary_score': True, },
                course_id=course_id, ),
            cols=[TextColumn(name='task_name', header=_('Task name')),
                  DatetimeColumn(name='submit_date', header=_('Submit time')),
                  TextColumn(name='user_first_name', header=_('Submitter first name')),
                  TextColumn(name='user_last_name', header=_('Submitter last name')),
                  TextColumn(name='summary_score', header=_('Score'))],
            title=_('All results'),
            refresh_button=True,
            paging=TableWidgetPaging(page_length=50,
                                     allow_length_change=True,
                                     length_change_options=[10, 25, 50, 100]),
            link_format_string=f'/course/{course_id}/submit/[[id]]/',
        )
        self.add_widget(context, results_table)

        return context


class CourseTask(BaCa2LoggedInView):
    template_name = 'course_task.html'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """
        Checks if the user is an admin of the course or a superuser. If so, redirects to the course
        admin page. If not, checks if the user is a member of the course. If so, returns the course
        page. If not, returns an HTTP 403 Forbidden error.
        """
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))
        # if course.user_is_admin(request.user) or request.user.is_superuser:
        #     return redirect('course:course-admin', course_id=course.id)
        if not course.user_is_member(request.user) and not request.user.is_superuser:
            return HttpResponseForbidden(_('You are neither a member of this course nor an admin.\n'
                                           'You are not allowed to view this page.'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        task_id = self.kwargs.get('task_id')
        task = ModelsRegistry.get_task(task_id, course_id)

        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=['Description', 'Submit', 'My results'], )

        self.add_widget(context, sidenav)

        # description
        package = task.package_instance.package

        description_extension = package.doc_extension()
        description_file = package.doc_path(description_extension)
        if package.doc_has_extension('pdf'):
            pdf_path = task.package_instance.pdf_docs_path
        if description_extension == 'pdf':
            description_file = pdf_path
        description_displayer = MarkupDisplayer(name='description', file_path=description_file)
        self.add_widget(context, description_displayer)

        # submit
        submit_form = CreateSubmitFormWidget(request=self.request,
                                             course_id=course_id, )
        self.add_widget(context, submit_form)

        # results list
        results_table = TableWidget(
            name='results_table_widget',
            request=self.request,
            data_source=SubmitModelView.get_url(
                mode=BaCa2ModelView.GetMode.FILTER,
                query_params={'task__pk': task_id,
                              'usr': self.request.user.id},
                serialize_kwargs={'show_user': False},
                course_id=course_id,
            ),
            cols=[
                DatetimeColumn(name='submit_date', header=_('Submit time')),
                TextColumn(name='final_score', header=_('Percentage')),
                TextColumn(name='task_score', header=_('Task score')),
            ],
            title=f"{_('My results')} - {task.task_name}",
            refresh_button=True,
            link_format_string=f'/course/{course_id}/submit/[[id]]/',
        )
        self.add_widget(context, results_table)

        return context


class CourseTaskAdmin(BaCa2LoggedInView, UserPassesTestMixin):
    """
    View for admins of a course. Only accessible if the user is an admin of the course or a
    superuser.
    """

    template_name = 'course_task_admin.html'

    def test_func(self) -> bool:
        """
        Test function for UserPassesTestMixin.

        :return: `True` if the user is an admin of the course or a superuser, `False` otherwise.
        :rtype: bool
        """
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))
        return course.user_is_admin(self.request.user) or self.request.user.is_superuser

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        task_id = self.kwargs.get('task_id')

        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=['Description', 'Student submissions', 'Edit'], )

        self.add_widget(context, sidenav)

        # Add widget, generating task description from file
        submissions_table = TableWidget(
            name='submissions_table_widget',
            request=self.request,
            data_source=SubmitModelView.get_url(
                mode=BaCa2ModelView.GetMode.FILTER,
                query_params={'task__id': task_id},
                serialize_kwargs={'add_summary_score': True},
                course_id=course_id,
            ),
            cols=[
                DatetimeColumn(name='submit_date', header=_('Submit time')),
                TextColumn(name='user_first_name', header=_('Submitter name')),
                TextColumn(name='user_last_name', header=_('Submitter last name')),
                TextColumn(name='summary_score', header=_('Score')),
            ],
            title=_('Submissions'),
            refresh_button=True,
            link_format_string=f'/course/{course_id}/submit/[[id]]/',
        )
        self.add_widget(context, submissions_table)

        return context


class RoundEditView(BaCa2LoggedInView, UserPassesTestMixin):
    template_name = 'course_edit_round.html'

    def test_func(self) -> bool:
        """
        Test function for UserPassesTestMixin.

        :return: `True` if the user is an admin of the course or a superuser, `False` otherwise.
        :rtype: bool
        """
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))
        return course.user_is_admin(self.request.user) or self.request.user.is_superuser

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        course_id = self.kwargs.get('course_id')
        course = ModelsRegistry.get_course(course_id)
        rounds = course.rounds()
        rounds = sorted(rounds, key=lambda x: x.name)
        round_names = [r.name for r in rounds]
        sidenav = SideNav(request=self.request,
                          collapsed=True,
                          tabs=round_names, )
        self.add_widget(context, sidenav)

        rounds_context = []

        for r in rounds:
            round_edit_form = EditRoundFormWidget(
                request=self.request,
                course_id=course_id,
                round_=r,
            )
            rounds_context.append({
                'tab_name': SideNav.normalize_tab_name(r.name),
                'round_name': r.name,
                'round_edit_form': round_edit_form,
            })
        context['rounds'] = rounds_context

        return context


class SubmitSummaryView(BaCa2LoggedInView):
    template_name = 'course_submit_summary.html'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        course_id = self.kwargs.get('course_id')
        submit_id = self.kwargs.get('submit_id')
        course = ModelsRegistry.get_course(course_id)
        submit = course.get_submit(submit_id)

        if course.user_is_admin(request.user) or request.user.is_superuser:
            self.kwargs['admin_access'] = True
        elif submit.user == request.user:
            self.kwargs['admin_access'] = False
        else:
            return HttpResponseForbidden(_('You are not allowed to view this page.'))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        submit_id = self.kwargs.get('submit_id')
        submit = ModelsRegistry.get_submit(submit_id, course_id)
        with InCourse(course_id):
            task = submit.task
        course = ModelsRegistry.get_course(course_id)

        summary_table = TableWidget(
            name='summary_table_widget',
            request=self.request,
            cols=[
                TextColumn(name='title', sortable=False),
                TextColumn(name='value', sortable=False)
            ],
            data_source=[
                {'title': _('Course'), 'value': course.name},
                {'title': _('Round'), 'value': task.round_.name},
                {'title': _('Task'), 'value': task.task_name},
                {'title': _('User'), 'value': submit.user.get_full_name()},
                {'title': _('Submit time'),
                 'value': submit.submit_date.strftime('%Y-%m-%d %H:%M:%S')},
                {'title': _('Score'), 'value': submit.summary_score},
            ],
            title=_('Summary') + f' - {_("submit")} #{submit.pk}',
            allow_global_search=False,
            allow_column_search=False,
            hide_col_headers=True,
            default_sorting=False,
        )
        self.add_widget(context, summary_table)

        sets = task.sets
        sets = sorted(sets, key=lambda x: x.short_name)
        sets_list = []
        for s in sets:
            set_context = {
                'set_name': s.short_name,
                'set_id': s.pk,
                'widgets': {'TableWidget': {}},
            }

            set_summary = TableWidget(
                name=f'set_{s.pk}_summary_table_widget',
                request=self.request,
                data_source=ResultModelView.get_url(
                    mode=BaCa2ModelView.GetMode.FILTER,
                    query_params={'submit': submit_id, 'test__test_set_id': s.pk},
                    course_id=course_id,
                ),
                cols=[
                    TextColumn(name='test_name', header=_('Test')),
                    TextColumn(name='f_status', header=_('Status')),
                    TextColumn(name='f_time_real', header=_('Time'), searchable=False),
                    TextColumn(name='f_runtime_memory', header=_('Memory'), searchable=False),
                ],
                title=f'{_("Set")} {s.short_name} - {_("weight:")} {s.weight}',
                allow_column_search=False,
                default_order_col='test_name',
            )
            self.add_widget(set_context, set_summary)
            set_context['table_widget'] = list(set_context['widgets']['TableWidget'].values())[0]
            sets_list.append(set_context)

        context['sets'] = sets_list

        return context
