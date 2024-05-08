import logging
import re
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView

from htbuilder import div, li, ul
from main.models import Announcement, Course, Role, User
from util import decode_url_to_dict, encode_dict_to_url
from util.models_registry import ModelsRegistry
from util.responses import BaCa2JsonResponse, BaCa2ModelResponse
from util.views import BaCa2ContextMixin, BaCa2LoggedInView, BaCa2ModelView
from widgets.forms import FormWidget
from widgets.forms.course import (
    AddMemberForm,
    AddMembersFromCSVForm,
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
    CreateAnnouncementForm,
    CreateAnnouncementWidget,
    CreateUser,
    CreateUserWidget,
    DeleteAnnouncementForm,
    EditAnnouncementForm,
    EditAnnouncementFormWidget
)
from widgets.listing import TableWidget, TableWidgetPaging, Timeline
from widgets.listing.columns import TextColumn
from widgets.listing.main import AnnouncementsTable
from widgets.listing.timeline import ReleaseEvent
from widgets.navigation import SideNav
from widgets.notification import AnnouncementBlock

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
                                      serialize_kwargs: dict,
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
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
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
            return AddMemberForm.handle_post_request(request)
        elif form_name == f'{Course.CourseAction.ADD_MEMBERS_CSV.label}_form':
            return AddMembersFromCSVForm.handle_post_request(request)
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
                                      serialize_kwargs: dict,
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
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
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
                                      serialize_kwargs: dict,
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
        :param serialize_kwargs: Kwargs passed to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
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


class AnnouncementModelView(BaCa2ModelView):
    """
    View used to retrieve serialized announcement model data to be displayed in the front-end and to
    interface between POST requests and model forms used to manage announcement instances.
    """

    MODEL = Announcement

    def post(self, request, **kwargs) -> BaCa2JsonResponse:
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

        if form_name == f'{Announcement.BasicAction.ADD.label}_form':
            return CreateAnnouncementForm.handle_post_request(request)
        if form_name == f'{Announcement.BasicAction.EDIT.label}_form':
            return EditAnnouncementForm.handle_post_request(request)
        if form_name == f'{Announcement.BasicAction.DEL.label}_form':
            return DeleteAnnouncementForm.handle_post_request(request)

        return self.handle_unknown_form(request, **kwargs)


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
        context['page_title'] = _('Login')

        self.add_widget(context, FormWidget(
            name='login_form',
            request=self.request,
            form=self.get_form(),
            button_text=_('Log in'),
            display_field_errors=False,
            live_validation=False,
        ))

        return context


class BaCa2LogoutView(RedirectView):
    """
    This class represents the logout view for the BaCa2 application. It extends the RedirectView
    from Django. It is responsible for logging out the user and redirecting them to the appropriate
    after logout page based on the type of user.
    """

    #: The URL to redirect to after logout for UJ users.
    url_uj = settings.OIDC_OP_LOGOUT_URL
    #: The URL to redirect to after logout for external users.
    url_ext = reverse_lazy('login')

    def get_redirect_url(self, *args, **kwargs) -> str:
        """
        Determines the URL to redirect to after logout based on the type of user. If the user is a
        UJ user, the URL to redirect to is the OIDC_OP_LOGOUT_URL from the settings.
        If the user is an external user, the URL to redirect to is the `login` URL.

        :return: The URL to redirect to after logout.
        :rtype: str
        """
        if self.request.user.is_uj_user:
            return self.url_uj
        return self.url_ext

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        """
        Handles the GET request for this view. Logs out the user and redirects them to the
        appropriate after-logout page. UJ users are redirected to the OIDC_OP_LOGOUT_URL from the
        settings, while external users are redirected to the `login` URL.

        :param request: The HTTP GET request object received by the view.
        :type request: HttpRequest
        :return: The HTTP response to redirect the user to the appropriate login page.
        :rtype: HttpResponseRedirect
        """
        resp = super().get(request, *args, **kwargs)
        logger.info(f'{resp.url} {request.user.is_uj_user}')
        logout(request)
        return resp


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
        context['page_title'] = _('Admin')

        sidenav = SideNav(request=self.request,
                          collapsed=False,
                          toggle_button=True,
                          tabs=['Courses', 'Users', 'Packages', 'Announcements'],
                          sub_tabs={'Users': ['New User', 'Users Table'],
                                    'Courses': ['New Course', 'Courses Table'],
                                    'Packages': ['New Package', 'Packages Table'],
                                    'Announcements': ['New Announcement', 'Announcements Table']})
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

        create_announcement_form = CreateAnnouncementWidget(request=self.request)
        self.add_widget(context, create_announcement_form)

        announcements_table = AnnouncementsTable(request=self.request)
        self.add_widget(context, announcements_table)

        return context


class AnnouncementEditView(BaCa2LoggedInView, UserPassesTestMixin):
    """
    Simple view for editing announcements. Accessible by superusers from the admin view
    announcements table widget.
    """

    template_name = 'announcement_edit.html'

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Edit Announcement')
        announcement_id = self.kwargs.get('announcement_id')
        edit_announcement_form = EditAnnouncementFormWidget(request=self.request,
                                                            announcement_id=announcement_id)
        self.add_widget(context, edit_announcement_form)
        return context


# ----------------------------------------- User views ----------------------------------------- #


class DashboardView(BaCa2LoggedInView):
    """
    Default home page view for BaCa2.

    See also:
        - :class:`BaCa2LoggedInView`
    """
    template_name = 'development_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcements = [a for a in Announcement.objects.all() if a.released]
        announcements.sort(reverse=True)
        self.add_widget(context, AnnouncementBlock(name='announcements',
                                                   announcements=announcements))
        context['user_first_name'] = self.request.user.first_name
        return context


class DevelopmentTimelineView(BaCa2LoggedInView):
    template_name = 'development_timeline.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        releases = [
            ReleaseEvent(tag='v.1.0-beta',
                         date='17-04-2024',
                         description=str(div('Otwarcie dostępu beta aplikacji dla członków kursu '
                                             'Metody Numeryczne')),
                         released=True),
            ReleaseEvent(tag='v.1.1-beta',
                         date='24-04-2024',
                         description=str(div(
                             'Zmiany widoczne dla użytkowników:',
                             ul(
                                 li('Zamieszczenie planu rozwoju aplikacji na stronie'),
                             ),
                             'Zmiany wewnętrzne:',
                             ul(_class='mb-0')(
                                 li('Ustalenie planu rozwoju aplikacji'),
                                 li('Monitoring i optymalizacja systemu'),
                                 li('Zapewnienie poprawnego zapisu plików do MEDIA files'),
                                 li('Opracowanie projektu nowego package managera')
                             )
                         )),
                         released=True),
            ReleaseEvent(tag='v.1.2-beta',
                         date='08-05-2024',
                         description=str(div(
                             'Zmiany widoczne dla użytkowników:',
                             ul(
                                 li('Dodanie strony "przerwa techniczna"'),
                                 li('Dodanie panelu ogłoszeń na stronie głównej'),
                                 li('Dodanie współczynnika spadku do tabeli zadań'),
                                 li('Dodanie statusu rozwiązania zadania w tabeli zadań'),
                                 li('Poprawiono wyświetlanie stopki na urządzeniach '
                                    'z mniejszą rozdzielczością ekranu')
                             ),
                             'Zmiany wewnętrzne:',
                             ul(_class='mb-0')(
                                 li('Uprzątnięcie po wycieku danych'),
                                 li('Zarządzanie ogłoszeniami z poziomu panelu admina'),
                                 li('Dodanie autodetekcji niewysłanych zgłoszeń i obsługa ich')
                             )
                         )),
                         released=True),
            ReleaseEvent(tag='v.1.3-beta',
                         date='15-05-2024',
                         description=str(div(
                             'Zmiany widoczne dla użytkowników:',
                             ul(
                                 li('Kolorowanie wierszy w tabelach zadań i submisji w zależności '
                                    'od uzyskanego wyniku'),
                                 li('Tłumaczenie aplikacji na język polski'),
                             ),
                             'Zmiany wewnętrzne:',
                             ul(_class='mb-0')(
                                 li('Refaktoryzacja logiki widoków z pomocą wzorca Builder'),
                                 li('Usprawnienie logiki walidacji "live" w formularzach'),
                                 li('Zapewnienie poprawnego zapisu plików do MEDIA files'),
                                 li('Przygotowanie konfiguracji deploymentu aplikacji na serwerze '
                                    'z pomocą systemu Kubernetes'),
                                 li('Praca nad rozwojem nowego package managera')
                             )
                         )),
                         released=False),

            ReleaseEvent(tag='v.1.4-beta',
                         date='22-05-2024',
                         description=str(div(
                             'Zmiany widoczne dla użytkowników:',
                             ul(
                                 li('Dodanie funkcjonalności grupowania wierszy w tabelach'),
                             ),
                             'Zmiany wewnętrzne:',
                             ul(_class='mb-0')(
                                 li('Finalizacja konfiguracji oraz deployment na serwerze '
                                    'produkcyjnym z pomocą systemu Kubernetes'),
                                 li('Finalizacja refaktoryzacji logiki formularzy'),
                                 li('Implementacja nowego package managera'),
                             )
                         )),
                         released=False),
            ReleaseEvent(tag='v.1.5-beta',
                         date='29-05-2024',
                         description=str(div(
                             'Zmiany widoczne dla użytkowników:',
                             ul(
                                 li('Rozbudowanie funkcjonalności tabeli przez wprowadzenie '
                                    'rozwijanych wierszy i formularzy w formie popup'),
                                 li('Poprawki dotyczące UI/UX'),
                             ),
                             'Zmiany wewnętrzne:',
                             ul(_class='mb-0')(
                                 li('Zmiany w brokerze w celu sprawniejszego wykorzystania '
                                    'systemu KOLEJKA dzięki multitask support'),
                             )
                         )),
                         released=False),
        ]
        self.add_widget(context, Timeline(name='dev_timeline',
                                          events=releases,
                                          scroll_to='v.1.2-beta'))
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
        context['page_title'] = _('Courses')

        self.add_widget(context, TableWidget(
            name='courses_table_widget',
            request=self.request,
            title='Your courses',
            data_source=CourseModelView.get_url(mode=BaCa2ModelView.GetMode.FILTER,
                                                filter_params={'role_set__user': user_id},
                                                serialize_kwargs={'user': user_id}),
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
        role = ModelsRegistry.get_role(self.kwargs.get('role_id'))
        course = role.course
        self.request.course_id = course.id
        context = super().get_context_data(**kwargs)
        user = getattr(self.request, 'user')
        sidenav_tabs = ['Overview', 'Members']
        context['page_title'] = f'{course.name} - {role.name}'

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
            table_height=35
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
        context['page_title'] = _('Profile')
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
            allow_global_search=False,
            hide_col_headers=True,
            default_sorting=False,
        )
        self.add_widget(context, data_summary)

        data_change = ChangePersonalDataWidget(request=self.request)
        self.add_widget(context, data_change)

        if not user.is_uj_user:
            self.add_widget(context, FormWidget(
                name='change_password_form_widget',
                request=self.request,
                form=PasswordChangeForm(user),
                button_text=_('Change password'),
                display_field_errors=False,
                live_validation=False,
                post_target_url=reverse_lazy('main:change-password'),
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
