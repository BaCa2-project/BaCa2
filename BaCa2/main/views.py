import logging
from typing import List

from django.contrib.auth import logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView, View

from main.models import Course, User
from util.responses import BaCa2ModelResponse
from util.views import BaCa2ContextMixin, BaCa2LoggedInView, BaCa2ModelView
from widgets.forms import FormWidget
from widgets.forms.course import CreateCourseForm, CreateCourseFormWidget, DeleteCourseForm
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.columns import TextColumn
from widgets.navigation import SideNav

logger = logging.getLogger(__name__)


# ----------------------------------------- Model views ---------------------------------------- #

class CourseModelView(BaCa2ModelView):
    """
    View for managing courses and retrieving their data.

    See:
        - :class:`BaCa2ModelView`
    """

    MODEL = Course

    def check_get_filtered_permission(self,
                                      query_params: dict,
                                      query_result: List[Course],
                                      request,
                                      **kwargs) -> bool:
        """
        :param query_params: Query parameters used to filter the retrieved query set.
        :type query_params: dict
        :param query_result: Query set retrieved using the query parameters evaluate to a list.
        :type query_result: List[Course]
        :param request: HTTP request received by the view.
        :type request: HttpRequest
        :return: `True` if the user has permission to view all courses or if the user is a member of
            every course retrieved by the query, `False` otherwise.
        :rtype: bool
        """
        if self.check_get_all_permission(request, **kwargs):
            return True
        for course in query_result:
            if not course.user_is_member(request.user):
                return False
        return True

    def check_get_excluded_permission(self, query_params, query_result, request, **kwargs) -> bool:
        """
        :param query_params: Query parameters used to filter the retrieved query set.
        :type query_params: dict
        :param query_result: Query set retrieved using the query parameters evaluate to a list.
        :type query_result: List[Course]
        :param request: HTTP request received by the view.
        :type request: HttpRequest
        :return: `True` if the user has permission to view all courses or if the user is a member of
            every course retrieved by the query, `False` otherwise.
        :rtype: bool
        """
        return self.check_get_filtered_permission(query_params, query_result, request, **kwargs)

    def post(self, request, **kwargs) -> BaCa2ModelResponse:
        """
        Handles a POST request received from a course model form. The method calls on the
        handle_post_request method of the form class used to generate the widget from which the
        request originated.

        :return: JSON response with the result of the action in the form of status and message
            strings.
        :rtype: :class:`BaCa2ModelResponse`
        """
        if request.POST.get('form_name') == 'add_course_form':
            return CreateCourseForm.handle_post_request(request)
        if request.POST.get('form_name') == 'delete_course_form':
            return DeleteCourseForm.handle_post_request(request)
        else:
            return self.handle_unknown_form(request, **kwargs)


class UserModelView(BaCa2ModelView):
    """
    View for managing users and retrieving their data.

    See:
        - :class:`BaCa2ModelView`
    """

    MODEL = User

    def check_get_filtered_permission(self, query_params, query_result, request, **kwargs) -> bool:
        """
        :param query_params: Query parameters used to filter the retrieved query set.
        :type query_params: dict
        :param query_result: Query set retrieved using the query parameters evaluate to a list.
        :type query_result: List[User]
        :param request: HTTP request received by the view.
        :type request: HttpRequest
        :return: `True` if the user has permission to view all users, is a course admin or if
            the only user retrieved by the query is the requesting user, `False` otherwise.
        :rtype: bool
        """
        if self.check_get_all_permission(request, **kwargs):
            return True
        if request.user.is_course_admin():
            return True
        if len(query_result) == 1 and query_result[0] == request.user:
            return True

    def check_get_excluded_permission(self, query_params, query_result, request, **kwargs) -> bool:
        """
        :param query_params: Query parameters used to filter the retrieved query set.
        :type query_params: dict
        :param query_result: Query set retrieved using the query parameters evaluate to a list.
        :type query_result: List[User]
        :param request: HTTP request received by the view.
        :type request: HttpRequest
        :return: `True` if the user has permission to view all users, is a course admin or if
            the only user retrieved by the query is the requesting user, `False` otherwise.
        :rtype: bool
        """
        return self.check_get_filtered_permission(query_params, query_result, request, **kwargs)

    def post(self, request, **kwargs) -> BaCa2ModelResponse:
        """
        Handles a POST request received from a user model form. The method calls on the
        handle_post_request method of the form class used to generate the widget from which the
        request originated.

        :return: JSON response with the result of the action in the form of status and message
            strings.
        :rtype: :class:`BaCa2ModelResponse`
        """
        pass


# --------------------------------------- Authentication --------------------------------------- #

class LoginRedirectView(RedirectView):
    """
    Redirects to BaCa2 login page.
    """

    # Redirect target.
    url = reverse_lazy('login')


class BaCa2LoginView(BaCa2ContextMixin, LoginView):
    """
    Login view for BaCa2. Contains a login form widget and theme switch. Redirects to dashboard on
    successful login or if user is already logged in (redirect target is set using the
    'LOGIN_REDIRECT_URL' variable in project's 'settings.py' file).
    """

    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.add_widget(context, FormWidget(
            name='login_form',
            request=self.request,
            form=self.get_form(),
            button_text='Zaloguj',
            display_field_errors=False,
            live_validation=False,
        ))

        return context


class BaCa2LogoutView(RedirectView):
    """
    Logout view for BaCa2. Redirects to login page on successful logout.
    """

    # Redirect target.
    url = reverse_lazy('login')

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        """
        Logs out the user and redirects to login page.
        """
        logout(request)
        return super().get(request, *args, **kwargs)


class UJLogin(View):
    @staticmethod
    def post(request, *args, **kwargs) -> None:
        logger.debug(f'{request.POST}')


# ----------------------------------------- Admin view ----------------------------------------- #


class AdminView(BaCa2LoggedInView, UserPassesTestMixin):
    """
    Admin view for BaCa2 used to manage users, courses and packages. Can only be accessed by
    superusers.

    See also:
        - :class:`BaCa2LoggedInView`
    """
    template_name = 'admin.html'

    def test_func(self) -> bool:
        """
        Test function for UserPassesTestMixin. Checks if the user is a superuser.

        :return: `True` if the user is a superuser, `False` otherwise.
        :rtype: bool
        """
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sidenav = SideNav(request=self.request,
                          collapsed=False,
                          toggle_button=True,
                          tabs=['Courses', 'Users', 'Packages'],
                          sub_tabs={'Users': ['New User', 'Users Table'],
                                    'Courses': ['New Course', 'Courses Table'],
                                    'Packages': ['New Package', 'Packages Table']})
        self.add_widget(context, sidenav)

        if not self.has_widget(context, FormWidget, 'create_course_form_widget'):
            self.add_widget(context, CreateCourseFormWidget(request=self.request))

        self.add_widget(context, TableWidget(
            name='courses_table_widget',
            title='Courses',
            request=self.request,
            data_source_url=CourseModelView.get_url(),
            cols=[
                TextColumn(name='id',
                           header='ID',
                           searchable=True,
                           auto_width=False,
                           width='4rem'),
                TextColumn(name='name', header='Name', searchable=True),
                TextColumn(name='USOS_course_code', header='Course code', searchable=True),
                TextColumn(name='USOS_term_code',
                           header='Term code',
                           searchable=True,
                           auto_width=False,
                           width='8rem'),
            ],
            allow_select=True,
            allow_delete=True,
            delete_form=DeleteCourseForm(),
            data_post_url=CourseModelView.post_url(),
            paging=TableWidgetPaging(10, False),
            link_format_string='/course/[[id]]/',
        ))

        return context


# ----------------------------------------- User views ----------------------------------------- #


class DashboardView(BaCa2LoggedInView):
    """
    Default home page view for BaCa2.

    See also:
        - :class:`BaCa2LoggedInView`
    """
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CoursesView(BaCa2LoggedInView):
    """
    View displaying all courses available to the user.

    See also:
        - :class:`BaCa2LoggedInView`
    """
    template_name = 'courses.html'

    def get_context_data(self, **kwargs):
        user_id = self.request.user.id
        context = super().get_context_data(**kwargs)
        self.add_widget(context, TableWidget(
            name='courses_table_widget',
            request=self.request,
            title='Your courses',
            data_source_url=CourseModelView.get_url(mode=BaCa2ModelView.GetMode.FILTER,
                                                    query_params={'role_set__user': user_id},
                                                    serialize_kwargs={'user': user_id}),
            allow_column_search=True,
            cols=[
                TextColumn(name='name', header='Name', searchable=True),
                TextColumn(name='USOS_term_code', header='Semester', searchable=True),
                TextColumn(name='user_role', header='Your role', searchable=True),
            ],
            link_format_string='/course/[[id]]/',
        ))
        return context


# ----------------------------------------- Util views ----------------------------------------- #


def change_theme(request) -> JsonResponse:
    """
    Placeholder functional view for changing the website theme.

    :return: JSON response with the result of the action in the form of status string.
    :rtype: JsonResponse
    """
    if request.method == 'POST':
        if request.user.is_authenticated:
            theme = request.POST.get('theme')
            request.user.user_settings.theme = theme
            request.user.user_settings.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})
