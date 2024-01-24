from django.db.models import QuerySet
from django.views.generic.base import RedirectView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from util.models_registry import ModelsRegistry
from util.views import BaCa2ContextMixin, BaCa2LoggedInView, BaCa2ModelView
from main.models import Course, User
from widgets.navigation import SideNav
from widgets.forms import FormWidget
from widgets.forms.base import BaCa2ModelFormResponse
from widgets.forms.course import CreateCourseForm, CreateCourseFormWidget, DeleteCourseForm
from widgets.listing import TableWidget, TableWidgetPaging, ModelDataSource
from widgets.listing.columns import TextColumn


# ----------------------------------------- Model views ---------------------------------------- #

class CourseModelView(BaCa2ModelView):
    """
    View for managing courses and retrieving their data.

    See:
        - :class:`BaCa2ModelView`
    """

    MODEL = Course

    def get(self, request, **kwargs) -> JsonResponse:
        """
        Depending on the GET request parameters, the method retrieves data:
            - of all courses if no parameters are specified (the requesting user must have
                permission to view courses),
            - of a single course if the 'target' parameter is specified (the requesting user must
                have permission to view courses),
            - of all courses to which the user is assigned if the 'user' parameter is specified
                (the requesting user must be the same user or a superuser),
            - of a single course to which the user is assigned if the 'user' and 'target'
                parameters are specified (the requesting user must be the same user or a
                superuser)

        :return: JSON response with the result of the action in the form of status and message
            strings (and data list if the request is valid).
        :rtype: JsonResponse
        """
        user = request.GET.get('user')

        if not user:
            return super().get(request, **kwargs)

        user = ModelsRegistry.get_user(int(user))

        if user != request.user and not request.user.is_superuser:
            return JsonResponse({'status': 'error',
                                 'message': _('Permission denied. User id does not match.')})

        if request.GET.get('target'):
            try:
                target = Course.objects.get(id=request.GET.get('target'))
            except Course.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': _('Target not found.')})

            if not user.can_access_course(target):
                return JsonResponse({'status': 'error',
                                     'message': _('User is not assigned to this course')})

            return JsonResponse(
                {'status': 'ok',
                 'message': _('Successfully data for the specified course to which the user is '
                              'assigned'),
                 'data': [target.get_data(user=user)]}
            )

        return JsonResponse(
            {'status': 'ok',
             'message': _('Successfully retrieved data for all courses to which the user is '
                          'assigned.'),
             'data': [instance.get_data(user=user) for instance in user.get_courses()]}
        )

    def post(self, request, **kwargs) -> BaCa2ModelFormResponse:
        """
        Handles a POST request received from a course model form. The method calls on the
        handle_post_request method of the form class used to generate the widget from which the
        request originated.

        :return: JSON response with the result of the action in the form of status and message
            strings.
        :rtype: :class:`BaCa2ModelFormResponse`
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

    def get(self, request, **kwargs) -> JsonResponse:
        """
        Depending on the GET request parameters, the method retrieves data:
            - of all users if no parameters are specified (the requesting user must have permission
                to view users),
            - of a single user if the 'target' parameter is specified (the requesting user must
                have permission to view users),
            - of all users assigned to a course if the 'course' parameter is specified (the
                requesting user must be an admin of the course or a superuser),
            - of a single user assigned to a course if the 'course' and 'target' parameters are
                specified (the requesting user must be an admin of the course or a superuser)
            - of all users not assigned to a course if the 'not_in_course' parameter is specified
                (the requesting user must have permission to view users),

        :return: JSON response with the result of the action in the form of status and message
            strings (and data list if the request is valid).
        :rtype: JsonResponse
        """
        course = request.GET.get('course')
        not_in_course = request.GET.get('not_in_course')

        if not_in_course:
            if not self.test_view_permission(request, **kwargs):
                return JsonResponse({'status': 'error',
                                     'message': _('Permission denied. You are not allowed to view '
                                                  'users.')})
            not_in_course = int(not_in_course)
            return JsonResponse({
                'status': 'ok',
                'message': _('Successfully retrieved data for all users not assigned to a course.'),
                'data': [user.get_data() for user in self._get_users_not_in_course(not_in_course)]
            })

        if not course:
            return super().get(request, **kwargs)

        course = ModelsRegistry.get_course(int(course))

        if not course.user_is_admin(request.user) and not request.user.is_superuser:
            return JsonResponse({'status': 'error',
                                 'message': _('Permission denied. You are not an admin of this '
                                              'course or a superuser.')})

        if request.GET.get('target'):
            try:
                target = User.objects.get(id=request.GET.get('target'))
            except Course.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': _('Target not found.')})

            if not course.user_is_member(target):
                return JsonResponse({'status': 'error',
                                     'message': _('User whose data you are trying to access is '
                                                  'not a member of this course')})

            return JsonResponse(
                {'status': 'ok',
                 'message': _('Successfully retrieved data for the specified user assigned to the '
                              'specified course.'),
                 'data': [target.get_data(course=course)]}
            )

        return JsonResponse(
            {'status': 'ok',
             'message': _('Successfully retrieved data for all users assigned to the specified '
                          'course.'),
             'data': [instance.get_data(course=course) for instance in course.members()]}
        )

    @staticmethod
    def _get_users_not_in_course(course_id: int) -> QuerySet[User]:
        """
        Returns a QuerySet of all users not assigned to a course.

        :param course_id: ID of the course.
        :type course_id: int
        :return: QuerySet of all users not assigned to the course.
        :rtype: QuerySet[:class:`User`]
        """
        course = ModelsRegistry.get_course(course_id)
        return User.objects.exclude(id__in=course.members().values_list('id', flat=True))

    def post(self, request, **kwargs) -> BaCa2ModelFormResponse:
        """
        Handles a POST request received from a user model form. The method calls on the
        handle_post_request method of the form class used to generate the widget from which the
        request originated.

        :return: JSON response with the result of the action in the form of status and message
            strings.
        :rtype: :class:`BaCa2ModelFormResponse`
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
                          tabs=['Users', 'Courses', 'Packages'],
                          sub_tabs={'Users': ['New User', 'Users Table'],
                                    'Courses': ['New Course', 'Courses Table'],
                                    'Packages': ['New Package', 'Packages Table']})
        self.add_widget(context, sidenav)

        if not self.has_widget(context, FormWidget, 'create_course_form_widget'):
            self.add_widget(context, CreateCourseFormWidget(request=self.request))

        self.add_widget(context, TableWidget(
            request=self.request,
            data_source=ModelDataSource(Course),
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
        url_kwargs = {'user': self.request.user.id}
        context = super().get_context_data(**kwargs)
        self.add_widget(context, TableWidget(
            request=self.request,
            title='Your courses',
            data_source=ModelDataSource(Course, **url_kwargs),
            allow_column_search=True,
            cols=[
                TextColumn(name='name', header='Name', searchable=True),
                TextColumn(name='user_role', header='Your role', searchable=True),
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
