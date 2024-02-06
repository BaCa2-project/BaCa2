import inspect
from abc import ABC, ABCMeta
from typing import Callable, List, Union

import django.db.models
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from course.models import Round
from course.routing import InCourse
from main.views import UserModelView
from util.models_registry import ModelsRegistry
from util.views import BaCa2LoggedInView, BaCa2ModelView
from widgets.forms.course import AddMembersFormWidget
from widgets.listing import TableWidget
from widgets.listing.columns import TextColumn
from widgets.navigation import SideNav

# ----------------------------------------- Model views ---------------------------------------- #

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
    def url(cls, **kwargs) -> str:
        course_id = kwargs.get('course_id')
        if not course_id:
            raise cls.MissingCourseId('Course id required to construct URL')

        return f'/course/{course_id}/models/{cls.MODEL._meta.model_name}'


class RoundModelView(CourseModelView, metaclass=ReadCourseViewMeta):
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
                                    'Tasks': ['View tasks', 'Add task']})
        self.add_widget(context, sidenav)

        members_table = TableWidget(
            name='members_table_widget',
            request=self.request,
            data_source_url=UserModelView.get_url(),  # TODO: exclude course members
            cols=[TextColumn(name='first_name', header=_('First name')),
                  TextColumn(name='last_name', header=_('Last name')),
                  TextColumn(name='email', header=_('Email address')),
                  TextColumn(name='user_role', header=_('Role'))],
            title=_('Course members'),
        )
        self.add_widget(context, members_table)

        add_members_form = AddMembersFormWidget(request=self.request, course_id=course_id)
        self.add_widget(context, add_members_form)

        return context
