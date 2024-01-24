from abc import ABC, abstractmethod

from django.views.generic.base import RedirectView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from BaCa2.choices import BasicPermissionType
from util.models import model_cls
from util.models_registry import ModelsRegistry
from util.views import BaCa2ContextMixin, BaCa2LoggedInView
from main.models import Course, User
from widgets.navigation import SideNav
from widgets.forms import FormWidget
from widgets.forms.base import BaCa2FormResponse, BaCa2ModelFormResponse
from widgets.forms.course import CreateCourseForm, CreateCourseFormWidget, DeleteCourseForm
from widgets.listing import TableWidget, TableWidgetPaging, ModelDataSource
from widgets.listing.columns import TextColumn


# ----------------------------------------- Model views ---------------------------------------- #

class BaCa2ModelView(LoginRequiredMixin, View, ABC):
    """
    Base class for all views used to manage models and retrieve their data from the front-end. GET
    requests directed at this view are used to retrieve data while POST requests are handled in
    accordance with the particular model form from which they originate.

    The view itself does not interface with model managers directly outside of retrieving data.
    Instead, it acts as an interface between POST requests and form classes which handle them.

    see:
        - :class:`widgets.forms.base.BaCa2ModelForm`
        - :class:`widgets.forms.base.BaCa2ModelFormResponse`
    """

    class ModelViewException(Exception):
        """
        Exception raised when an error related to retrieving data or handling POST requests in
        a model view occurs.
        """
        pass

    #: Model class which the view manages.
    MODEL: model_cls = None

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

    @abstractmethod
    def post(self, request, **kwargs) -> JsonResponse:
        """
        Receives a post request from a model form and calls on its handle_post_request method to
        validate and process the request.

        :return: JSON response with the result of the action in the form of status and message
            string
        :rtype: JsonResponse
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @classmethod
    def test_view_permission(cls, request, **kwargs) -> bool:
        """
        Checks if the user has permission to view data of the model class managed by the view.

        :return: `True` if the user has permission, `False` otherwise.
        :rtype: bool
        """
        return request.user.has_basic_model_permissions(cls.MODEL, BasicPermissionType.VIEW)

    @classmethod
    def handle_unknown_form(cls, request, **kwargs) -> BaCa2ModelFormResponse:
        """
        Generates a JSON response returned when the post request contains an unknown form name.

        :return: Error JSON response.
        :rtype: :class:`BaCa2ModelFormResponse`
        """
        return BaCa2ModelFormResponse(
            model=cls.MODEL,
            action=request.POST.get('action', ''),
            status=BaCa2FormResponse.Status.ERROR,
            message=_(f'Unknown form: {request.POST.get("form_name")}')
        )


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
            - of all courses if no parameters are specified (the user must have permission to view
                courses),
            - of a single course if the 'target' parameter is specified (the user must have
                permission to view courses),
            - of all courses to which the user is assigned if the 'user' parameter is specified
            - of a single course to which the user is assigned if the 'user' and 'target'
                parameters are specified

        :return: JSON response with the result of the action in the form of status and message
            strings (and data list if the request is valid).
        :rtype: JsonResponse
        """
        user = request.GET.get('user')

        if not user:
            return super().get(request, **kwargs)

        user = ModelsRegistry.get_user(int(user))

        if user != request.user:
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
