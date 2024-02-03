from abc import ABC

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from main.views import UserModelView
from util.models_registry import ModelsRegistry
from util.views import BaCa2LoggedInView, BaCa2ModelView
from widgets.forms.course import AddMembersFormWidget
from widgets.listing import TableWidget
from widgets.listing.columns import TextColumn
from widgets.navigation import SideNav

# ----------------------------------------- Model views ---------------------------------------- #

class CourseModelView(BaCa2ModelView, ABC):
    ...


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
