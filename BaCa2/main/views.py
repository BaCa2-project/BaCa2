from django.views.generic.base import RedirectView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy

from util.views import BaCa2ContextMixin, BaCa2LoggedInView, BaCa2ModelView
from util.responses import BaCa2ModelResponse
from main.models import Course, User
from widgets.navigation import SideNav
from widgets.forms import FormWidget
from widgets.forms.course import CreateCourseForm, CreateCourseFormWidget, DeleteCourseForm
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.columns import TextColumn


# ----------------------------------------- Model views ---------------------------------------- #

class CourseModelView(BaCa2ModelView):
    """
    View for managing courses and retrieving their data.

    See:
        - :class:`BaCa2ModelView`
    """

    MODEL = Course

    def check_get_filtered_permission(self, query_params, query, request, **kwargs) -> bool:
        if self.check_get_all_permission(request, **kwargs):
            return True
        for course in query:
            if not course.user_is_member(request.user):
                return False
        return True

    def check_get_excluded_permission(self, query_params, query, request, **kwargs) -> bool:
        return self.check_get_filtered_permission(query_params, query, request, **kwargs)

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

    def check_get_filtered_permission(self, query_params, query, request, **kwargs) -> bool:
        raise NotImplementedError()
        # TODO: Implement check_get_filtered_permission

    def check_get_excluded_permission(self, query_params, query, request, **kwargs) -> bool:
        raise NotImplementedError()
        # TODO: Implement check_get_excluded_permission

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
            paging=TableWidgetPaging(10, False),
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
        context = super().get_context_data(**kwargs)
        self.add_widget(context, TableWidget(
            name='courses_table_widget',
            request=self.request,
            title='Your courses',
            data_source_url=CourseModelView.get_url(),  # TODO: Filter courses by user
            allow_column_search=True,
            cols=[
                TextColumn(name='name', header='Name', searchable=True),
                TextColumn(name='USOS_term_code', header='Semester', searchable=True),
            ],
            highlight_rows_on_hover=True,
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
