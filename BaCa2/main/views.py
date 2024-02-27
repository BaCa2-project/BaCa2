import logging
import re
from typing import Any, Dict, List

from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView, View

from main.models import Course, Role, User
from util import decode_url_to_dict, encode_dict_to_url
from util.models_registry import ModelsRegistry
from util.responses import BaCa2JsonResponse, BaCa2ModelResponse
from util.views import BaCa2ContextMixin, BaCa2LoggedInView, BaCa2ModelView
from widgets.forms import FormWidget
from widgets.forms.course import (
    AddMembersForm,
    AddRoleForm,
    AddRolePermissionsForm,
    AddRolePermissionsFormWidget,
    CreateCourseForm,
    CreateCourseFormWidget,
    DeleteCourseForm,
    DeleteRoleForm,
    RemoveMembersForm,
    RemoveRolePermissionsForm,
    RemoveRolePermissionsFormWidget
)
from widgets.forms.main import (
    ChangePersonalData,
    ChangePersonalDataWidget,
    CreateUser,
    CreateUserWidget
)
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.columns import TextColumn
from widgets.navigation import SideNav

logger = logging.getLogger(__name__)


# ----------------------------------------- Model views ---------------------------------------- #

class CourseModelView(BaCa2ModelView):
    """
    View used to retrieve serialized course model data to be displayed in the front-end and to
    interface between POST requests and model forms used to manage course instances.
    """

    MODEL = Course

    def check_get_filtered_permission(self,
                                      filter_params: dict,
                                      exclude_params: dict,
                                      query_result: List[Course],
                                      request,
                                      **kwargs) -> bool:
        """
        Method used to evaluate requesting user's permission to view the model instances matching
        the specified query parameters retrieved by the view if the user does not possess the 'view'
        permission for all model instances.

        :param filter_params: Query parameters used to construct the filter for the retrieved query
            set.
        :type filter_params: dict
        :param exclude_params: Query parameters used to construct the exclude filter for the
            retrieved query set.
        :type exclude_params: dict
        :param query_result: Query set retrieved using the specified query parameters evaluated to a
            list.
        :type query_result: List[:class:`Course`]
        :param request: HTTP GET request object received by the view.
        :type request: HttpRequest
        :return: `True` if the user is a member of all courses retrieved by the query, `False`
            otherwise.
        :rtype: bool
        """
        for course in query_result:
            if not course.user_is_member(request.user):
                return False
        return True

    def post(self, request, **kwargs) -> BaCa2ModelResponse:
        """
        Delegates the handling of the POST request to the appropriate form based on the `form_name`
        parameter received in the request.

        If the `course` parameter is present in the request, it is decoded and stored in the request
        object as a dictionary under the `course` attribute (required for request handling by
        course action forms).

        :param request: HTTP POST request object received by the view
        :type request: HttpRequest
        :return: JSON response to the POST request containing information about the success or
            failure of the request
        :rtype: :py:class:`JsonResponse`
        """
        params = request.GET.dict()

        if params.get('course'):
            request.course = decode_url_to_dict(params.get('course'))
        else:
            request.course = {}

        form_name = request.POST.get('form_name')

        if form_name == f'{Course.BasicAction.ADD.label}_form':
            return CreateCourseForm.handle_post_request(request)
        elif form_name == f'{Course.BasicAction.DEL.label}_form':
            return DeleteCourseForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.ADD_MEMBER.label}_form':
            return AddMembersForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.ADD_ROLE.label}_form':
            return AddRoleForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.DEL_ROLE.label}_form':
            return DeleteRoleForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.DEL_MEMBER.label}_form':
            return RemoveMembersForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.EDIT_ROLE.label}_form':
            if 'permissions_to_add' in request.POST:
                return AddRolePermissionsForm.handle_post_request(request)
            elif 'permissions_to_remove' in request.POST:
                return RemoveRolePermissionsForm.handle_post_request(request)

        return self.handle_unknown_form(request, **kwargs)

    @classmethod
    def post_url(cls, **kwargs) -> str:
        """
        :param kwargs: Additional parameters to be included in the url used in a POST request.
        :type kwargs: dict
        :return: URL to be used in a POST request.
        :rtype: str
        """
        url = super().post_url(**kwargs)
        if 'course_id' in kwargs:
            url += f'?{encode_dict_to_url("course", {"course_id": kwargs["course_id"]})}'
        return url


class UserModelView(BaCa2ModelView):
    """
    View used to retrieve serialized user model data to be displayed in the front-end and to
    interface between POST requests and model forms used to manage user instances.
    """

    MODEL = User

    def check_get_filtered_permission(self,
                                      filter_params: dict,
                                      exclude_params: dict,
                                      query_result: List[User],
                                      request,
                                      **kwargs) -> bool:
        """
        Method used to evaluate requesting user's permission to view the model instances matching
        the specified query parameters retrieved by the view if the user does not possess the 'view'
        permission for all model instances.

        :param filter_params: Query parameters used to construct the filter for the retrieved query
            set.
        :type filter_params: dict
        :param exclude_params: Query parameters used to construct the exclude filter for the
            retrieved query set.
        :type exclude_params: dict
        :param query_result: Query set retrieved using the specified query parameters evaluated to a
            list.
        :type query_result: List[:class:`User`]
        :param request: HTTP GET request object received by the view.
        :type request: HttpRequest
        :return: `True` if the user has the 'add_member' permission in one of their courses, if
            the user is the only record retrieved by the query, or if the request originated from a
            view related to a course the user has the 'view_member' permission for and all users
            retrieved by the query are members of the course, `False` otherwise.
        :rtype: bool
        """
        user = request.user

        if user.has_role_permission(Course.CourseAction.ADD_MEMBER.label):
            return True
        if len(query_result) == 1 and query_result[0] == user:
            return True

        refer_url = request.META.get('HTTP_REFERER')

        if bool(re.search(r'course/\d+/', refer_url)):
            course_id = re.search(r'course/(\d+)/', refer_url).group(1)
            course = Course.objects.get(pk=course_id)
            view_member = user.has_course_permission(Course.CourseAction.VIEW_MEMBER.label, course)

            if view_member and all([course.user_is_member(usr) for usr in query_result]):
                return True

        return False

    def post(self, request, **kwargs) -> BaCa2ModelResponse:
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

        if form_name == f'{User.BasicAction.ADD.label}_form':
            return CreateUser.handle_post_request(request)
        if form_name == f'{User.BasicAction.EDIT.label}_form':
            return ChangePersonalData.handle_post_request(request)

        return self.handle_unknown_form(request, **kwargs)


class RoleModelView(BaCa2ModelView):
    """
    View used to retrieve serialized role model data to be displayed in the front-end and to
    interface between POST requests and model forms used to manage role instances.
    """

    MODEL = Role

    def check_get_filtered_permission(self,
                                      filter_params: dict,
                                      exclude_params: dict,
                                      query_result: List[Role],
                                      request,
                                      **kwargs) -> bool:
        """
        Method used to evaluate requesting user's permission to view the model instances matching
        the specified query parameters retrieved by the view if the user does not possess the 'view'
        permission for all model instances.

        :param filter_params: Query parameters used to construct the filter for the retrieved query
            set.
        :type filter_params: dict
        :param exclude_params: Query parameters used to construct the exclude filter for the
            retrieved query set.
        :type exclude_params: dict
        :param query_result: Query set retrieved using the specified query parameters evaluated to a
            list.
        :type query_result: List[:class:`Role`]
        :param request: HTTP GET request object received by the view.
        :type request: HttpRequest
        :return: `True` if all retrieved roles belong to a course the user has the 'view_role'
            permission for, `False` otherwise.
        :rtype: bool
        """
        for role in query_result:
            course = role.course
            if not request.user.has_course_permission(Course.CourseAction.VIEW_ROLE.label, course):
                return False

        return True


class PermissionModelView(BaCa2ModelView):
    """
    View used to retrieve serialized permission model data to be displayed in the front-end and to
    interface between POST requests and model forms used to manage permission instances.
    """

    @staticmethod
    def get_data(instance: Permission, **kwargs) -> Dict[str, Any]:
        """
        :param instance: Permission instance to be serialized.
        :type instance: Permission
        :return: Serialized permission instance data.
        :rtype: dict
        """
        return {
            'id': instance.id,
            'name': instance.name,
            'content_type_id': instance.content_type.id,
            'codename': instance.codename,
        }

    MODEL = Permission
    GET_DATA_METHOD = get_data

    @classmethod
    def _url(cls, **kwargs) -> str:
        """
        :return: Base url for the view. Used by :meth:`get_url` method.
        """
        return f'/main/models/{cls.MODEL._meta.model_name}/'


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
            button_text=_('Login'),
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
        logger.warning(f'{request.POST}')


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
            data_source=CourseModelView.get_url(),
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

        users_table = TableWidget(
            name='users_table_widget',
            title='Users',
            request=self.request,
            data_source=UserModelView.get_url(),
            cols=[
                TextColumn(name='email', header=_('Email'), searchable=True),
                TextColumn(name='first_name', header=_('First name'), searchable=True),
                TextColumn(name='last_name', header=_('Last name'), searchable=True),
                TextColumn(name='f_is_superuser', header=_('Superuser'), searchable=True),
            ],
            paging=TableWidgetPaging(25, False),
        )
        self.add_widget(context, users_table)

        add_user_form = CreateUserWidget(request=self.request)
        self.add_widget(context, add_user_form)

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
            data_source=CourseModelView.get_url(mode=BaCa2ModelView.GetMode.FILTER,
                                                filter_params={'role_set__user': user_id},
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


class RoleView(BaCa2LoggedInView, UserPassesTestMixin):
    template_name = 'course_role.html'

    def test_func(self) -> bool:
        course = ModelsRegistry.get_role(self.kwargs.get('role_id')).course
        user = getattr(self.request, 'user')

        if course.user_is_admin(user) or user.is_superuser:
            return True

        if user.has_course_permission(Course.CourseAction.VIEW_ROLE.label, course):
            return True

        return False

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        role = ModelsRegistry.get_role(self.kwargs.get('role_id'))
        course = role.course
        user = getattr(self.request, 'user')
        sidenav_tabs = ['Overview', 'Members']

        # overview -------------------------------------------------------------------------------

        permissions_table = TableWidget(
            name='permissions_table_widget',
            title=_('Permissions'),
            request=self.request,
            data_source=PermissionModelView.get_url(
                mode=BaCa2ModelView.GetMode.FILTER,
                filter_params={'role': role.id}
            ),
            cols=[TextColumn(name='codename', header=_('Codename')),
                  TextColumn(name='name', header=_('Name'))],
            refresh_button=True,
            height_limit=35
        )
        self.add_widget(context, permissions_table)

        # members --------------------------------------------------------------------------------

        members_table = TableWidget(
            name='members_table_widget',
            title=_('Members'),
            request=self.request,
            data_source=UserModelView.get_url(
                mode=BaCa2ModelView.GetMode.FILTER,
                filter_params={'roles': role.id}
            ),
            cols=[TextColumn(name='email', header=_('Email')),
                  TextColumn(name='first_name', header=_('First name')),
                  TextColumn(name='last_name', header=_('Last name'))],
            refresh_button=True
        )
        self.add_widget(context, members_table)

        # add/remove permissions -----------------------------------------------------------------

        if user.has_course_permission(Course.CourseAction.EDIT_ROLE.label, course):
            sidenav_tabs.append('Add permissions')
            add_permissions_form = AddRolePermissionsFormWidget(request=self.request,
                                                                course_id=course.id,
                                                                role_id=role.id)
            self.add_widget(context, add_permissions_form)

            sidenav_tabs.append('Remove permissions')
            remove_permissions_form = RemoveRolePermissionsFormWidget(request=self.request,
                                                                      course_id=course.id,
                                                                      role_id=role.id)
            self.add_widget(context, remove_permissions_form)

        # sidenav --------------------------------------------------------------------------------

        sidenav = SideNav(request=self.request,
                          collapsed=False,
                          toggle_button=False,
                          tabs=sidenav_tabs)
        self.add_widget(context, sidenav)

        return context


class ProfileView(BaCa2LoggedInView):
    """
    View for managing user settings.

    See also:
        - :class:`BaCa2LoggedInView`
    """
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        sidenav = SideNav(
            request=self.request,
            tabs=['Profile', 'Security'],
        )
        self.add_widget(context, sidenav)

        data_summary = TableWidget(
            name='personal_data_table_widget',
            title=f"{_('Personal data')} - {user.first_name} {user.last_name}",
            request=self.request,
            cols=[
                TextColumn(name='description', sortable=False),
                TextColumn(name='value', sortable=False),
            ],
            data_source=[
                {'description': _('Email'), 'value': user.email},
                {'description': _('First name'), 'value': user.first_name},
                {'description': _('Last name'), 'value': user.last_name},
                {'description': _('Superuser'), 'value': user.is_superuser},
            ],
            allow_column_search=False,
            allow_global_search=False,
            hide_col_headers=True,
            default_sorting=False,
        )
        self.add_widget(context, data_summary)

        data_change = ChangePersonalDataWidget(request=self.request)
        self.add_widget(context, data_change)

        self.add_widget(context, FormWidget(
            name='change_password_form_widget',
            request=self.request,
            form=PasswordChangeForm(user),
            button_text=_('Change password'),
            display_field_errors=False,
            live_validation=False,
            post_target=reverse_lazy('main:change-password'),
        ))
        context['change_password_title'] = _('Change password')

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


def change_password(request) -> BaCa2JsonResponse:
    """
    Placeholder functional view for changing the user password.

    :return: JSON response with the result of the action in the form of status string.
    :rtype: BaCa2JsonResponse
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return BaCa2JsonResponse(status=BaCa2JsonResponse.Status.SUCCESS,
                                     message=_('Password changed.'))
        else:
            validation_errors = form.errors
            return BaCa2JsonResponse(status=BaCa2JsonResponse.Status.INVALID,
                                     message=_('Password not changed.'),
                                     errors=validation_errors)
