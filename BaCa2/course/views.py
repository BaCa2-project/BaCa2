from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin

from util.views import BaCa2LoggedInView
from util.models_registry import ModelsRegistry
from widgets.navigation import SideNav


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
            return HttpResponseForbidden('You are neither a member of this course nor an admin.\n'
                                         'You are not allowed to view this page.')
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
        return context
