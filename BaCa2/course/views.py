from abc import ABC

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.translation import gettext_lazy as _

from BaCa2.choices import BasicPermissionType
from main.models import User
from util.views import BaCa2LoggedInView, BaCa2ModelView
from util.models_registry import ModelsRegistry
from widgets.navigation import SideNav
from widgets.listing import TableWidget
from widgets.listing.data_sources import ModelDataSource
from widgets.listing.columns import TextColumn
from widgets.forms.course import AddMembersFormWidget


# ----------------------------------------- Model views ---------------------------------------- #

class CourseModelView(BaCa2ModelView, ABC):
    def get(self, request, **kwargs) -> JsonResponse:
        """
        Retrieves data of the instance(s) of the model class managed by the view if the requesting
        user has permission to access it. If the request kwargs contain a 'target' key, the method
        will return data of the instance of the model class with the id specified in the 'target'.

        :return: JSON response with the result of the action in the form of status and message
            strings (and data list if the request is valid).
        :rtype: JsonResponse

        :raises ModelViewException: If the model class managed by the view does not implement the
            method needed to gather data.
        """
        if not self.test_view_permission(request, **kwargs):
            return JsonResponse({'status': 'error', 'message': _('Permission denied.')})

        get_data_method = getattr(self.MODEL, 'get_data')

        if not get_data_method or not callable(get_data_method):
            raise BaCa2ModelView.ModelViewException(
                f'Model class managed by the {self.__class__.__name__} view does not '
                f'implement the `get_data` method needed to perform this action.'
            )

        if request.GET.get('target'):
            try:
                target = self.MODEL.objects.get(id=request.GET.get('target'))
            except self.MODEL.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': _('Target not found.')})

            return JsonResponse(
                {'status': 'ok',
                 'message': _('Successfully retrieved target model data.'),
                 'data': [target.get_data()]}
            )
        else:
            return JsonResponse(
                {'status': 'ok',
                 'message': _('Successfully retrieved data for all model instances'),
                 'data': [instance.get_data() for instance in self.MODEL.objects.all()]}
            )

    def test_view_permission(self, request, **kwargs) -> bool:
        """
        Checks if the user is authorized to view the data of the model class managed by the view.

        :return: `True` if the user has the view permission for this model or is an admin of the
            course this view belongs to, `False` otherwise.
        :rtype: bool
        """
        course = ModelsRegistry.get_course(self.kwargs.get('course_id'))
        if course.user_is_admin(request.user):
            return True
        return super().test_view_permission(request, **kwargs)


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
            data_source=ModelDataSource(model=User, **{'course': course_id}),
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
