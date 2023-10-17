from abc import ABC, abstractmethod
from typing import (Dict, Any, Type, List)

from django.views.generic.base import (TemplateView, RedirectView, View)
from django.contrib.auth.mixins import (LoginRequiredMixin, UserPassesTestMixin)
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import (JsonResponse, HttpResponseRedirect)
from django.http.request import HttpRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from util.models import model_cls
from main.models import (Course, User)
from widgets import forms
from widgets.base import Widget
from widgets.listing import TableWidget
from widgets.forms import FormWidget
from widgets.navigation import (NavBar, SideNav)
from widgets.forms.course import (NewCourseForm, NewCourseFormWidget)
from BaCa2.choices import PermissionTypes
from widgets.forms.base import TableSelectField


class BaCa2ModelView(LoginRequiredMixin, View, ABC):
    """
    Base class for all views used to manage models of given class from front-end. Provides methods
    for retrieving model data and interfacing with model managers to create, update and delete
    model instances. Implements simple logic for checking user permissions corresponding to the
    actions before executing them. If an inheriting class extends or changes the list of supported
    actions, it has to provide for each of them two corresponding methods, one for checking user
    permissions and one for executing the action unless it overrides the :py:meth:`post` method.

    The permission checking method has to have the following signature:
    `test_<action>_permission(self, request, **kwargs) -> bool`
    The action execution method has to have the following signature:
    `<action>(self, request, **kwargs) -> JsonResponse`
    """

    class ModelViewException(Exception):
        """
        Exception raised when model view-related error occurs.
        """
        pass

    #: Model class which the view manages.
    MODEL: model_cls = None
    #: Actions supported by the view.
    SUPPORTED_ACTIONS = ['create', 'update', 'delete']

    # ------------------------------------ Response methods ------------------------------------ #

    def get(self, request, **kwargs) -> JsonResponse:
        """
        Retrieves data of the instance(s) of the model class managed by the view if the requesting
        user has permission to access it. If the request kwargs contain a 'target' key, the method
        will return data of the instance of the model class with the id specified in the 'target'.
        The data is gathered using the :py:meth:`get_data` method of the model class.

        :return: JSON response with the result of the action in the form of status and message
        strings (and data dictionary if the request is valid).
        :rtype: JsonResponse

        :raises ModelViewException: If the model class managed by the view does not implement the
            method needed to gather data.
        """
        if not self.test_view_permission(request, **kwargs):
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'})

        if kwargs.get('target', None):
            get_data_method = getattr(self.MODEL, 'get_data')

            if not get_data_method or not callable(get_data_method):
                raise BaCa2ModelView.ModelViewException(
                    f'Model class managed by the {self.__class__.__name__} view does not '
                    f'implement the `get_data` method needed to perform this action.')

            try:
                target = self.MODEL.objects.get(id=kwargs['target'])
            except self.MODEL.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Target not found.'})
            return JsonResponse({'status': 'ok',
                                 'message': f'successfully retrieved data for a model instance '
                                            f'with id = {kwargs["target"]}',
                                 'data': [target.get_data()]})
        else:
            return JsonResponse({'status': 'ok',
                                 'message': f'successfully retrieved data for all model instances',
                                 'data': [instance.get_data() for instance in
                                          self.MODEL.objects.all()]})

    def post(self, request, **kwargs) -> JsonResponse:
        """
        Handles POST requests. Checks if the action specified within the request is supported and
        if the user has permission to perform it. If so, calls the corresponding method. If not,
        returns a JSON response with an error message.

        :return: JSON response with the result of the action in the form of status and message
        strings.
        :rtype: JsonResponse

        :raises NotImplementedError: If the action is supported but the corresponding permission
            test method and/or action method is not implemented.
        """
        if request.POST.get('action', None) not in self.SUPPORTED_ACTIONS:
            return JsonResponse({'status': 'error', 'message': 'Invalid action.'})

        permission_test_method = getattr(self, f'test_{request.POST.get("action")}_permission',
                                         None)

        if not permission_test_method or not callable(permission_test_method):
            raise NotImplementedError(
                f'Permission test method for {request.POST.get("action")} not implemented.')
        if not permission_test_method(request, **kwargs):
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'})

        action_method = getattr(self, request.POST.get('action'), None)

        if not action_method or not callable(action_method):
            raise NotImplementedError(
                f'Action method for {request.POST.get("action")} not implemented.')

        return action_method(request, **kwargs)

    @classmethod
    @abstractmethod
    def create(cls, request, **kwargs) -> JsonResponse:
        """
        Communicates with the model manager to create a new model instance using the data provided
        in the request. Must be implemented by inheriting classes.

        :return: JSON response with the result of the action in the form of status and message
        strings.
        :rtype: JsonResponse
        """

    @classmethod
    @abstractmethod
    def update(cls, request, **kwargs) -> JsonResponse:
        """
        Communicates with the model manager to update an existing model instance using the data
        provided in the request. Must be implemented by inheriting classes.

        :return: JSON response with the result of the action in the form of status and message
        strings.
        :rtype: JsonResponse
        """

    @classmethod
    @abstractmethod
    def delete(cls, request, **kwargs) -> JsonResponse:
        """
        Communicates with the model manager to delete an existing model instance using the data
        provided in the request. Must be implemented by inheriting classes.

        :return: JSON response with the result of the action in the form of status and message
        strings.
        :rtype: JsonResponse
        """

    @staticmethod
    def invalid_form_response(request, message: str = _('invalid form')) -> JsonResponse:
        # TODO
        return JsonResponse({'status': 'error', 'message': message})

    # ------------------------------------ Permission checks ----------------------------------- #

    @classmethod
    def test_create_permission(cls, request, **kwargs) -> bool:
        """
        Checks if the user has permission to create a new model instance.

        :return: `True` if the user has permission, `False` otherwise.
        :rtype: bool
        """
        return request.user.has_model_permissions(cls.MODEL, PermissionTypes.ADD)

    @classmethod
    def test_update_permission(cls, request, **kwargs) -> bool:
        """
        Checks if the user has permission to update an existing model instance.

        :return: `True` if the user has permission, `False` otherwise.
        :rtype: bool
        """
        return request.user.has_model_permissions(cls.MODEL, PermissionTypes.EDIT)

    @classmethod
    def test_delete_permission(cls, request, **kwargs) -> bool:
        """
        Checks if the user has permission to delete an existing model instance.

        :return: `True` if the user has permission, `False` otherwise.
        :rtype: bool
        """
        return request.user.has_model_permissions(cls.MODEL, PermissionTypes.DEL)

    @classmethod
    def test_view_permission(cls, request, **kwargs) -> bool:
        """
        Checks if the user has permission to view data of the model class managed by the view.

        :return: `True` if the user has permission, `False` otherwise.
        :rtype: bool
        """
        return request.user.has_model_permissions(cls.MODEL, PermissionTypes.VIEW)


class CourseModelView(BaCa2ModelView):
    MODEL = Course

    @classmethod
    def create(cls, request, **kwargs) -> JsonResponse:
        form = NewCourseForm(data=request.POST)

        if not form.is_valid():
            return BaCa2ModelView.invalid_form_response(request)

        Course.objects.create_course(
            name=form.cleaned_data['name'],
            short_name=form.cleaned_data.get('short_name', None),
            usos_course_code=form.cleaned_data.get('USOS_course_code', None),
            usos_term_code=form.cleaned_data.get('USOS_term_code', None),
        )

    def update(cls, request, **kwargs) -> JsonResponse:
        pass

    def delete(cls, request, **kwargs) -> JsonResponse:
        pass


class UserModelView(BaCa2ModelView):
    MODEL = User

    def create(cls, request, **kwargs) -> JsonResponse:
        pass

    def update(cls, request, **kwargs) -> JsonResponse:
        pass

    def delete(cls, request, **kwargs) -> JsonResponse:
        pass


class BaCa2CourseModelView(BaCa2ModelView, ABC):
    """
    Base class for views used to manage course-scope models from front-end.
    """
    # TODO: Implement permission tests


class BaCa2ContextMixin:
    """
    Context mixin for all BaCa2 views used to establish shared context dictionary structure and
    context gathering logic between different views. Provides a preliminary setup for the context
    dictionary and a method for adding widgets to it. The :py:meth:`get_context_data` method of
    this mixin calls on the :py:meth:`get_context_data` method of the other following ancestor in
    the MRO chain and as such it should precede in the parent list of the view class any other mixin
    or view which calls on that method.
    """

    class WidgetException(Exception):
        """
        Exception raised when widget-related error occurs.
        """
        pass

    # List of all widget types used in BaCa2 views.
    WIDGET_TYPES = [TableWidget, FormWidget, NavBar, SideNav]
    # List of all widgets which are unique (i.e. there can only be one instance of each widget type
    # can exist in the context dictionary).
    UNIQUE_WIDGETS = [NavBar, SideNav]
    # Default theme for users who are not logged in.
    DEFAULT_THEME = 'dark'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Returns a dictionary containing all the data required by the template to render the view.
        Calls on the `get_context_data` method of the other following ancestor (should there be
        one) in the MRO chain (As such, if this mixin precedes in the parent list of the view
        class an ancestor view whose context gathering is also necessary, it is enough to call on
        the `get_context_data` once through the super() method).

        :param kwargs: Keyword arguments passed to the `get_context_data` method of the other
            following ancestor in the MRO chain (should there be one).
        :type kwargs: dict

        :return: A dictionary containing data required by the template to render the view.
        :rtype: Dict[str, Any]

        :raises Exception: If no request object is found.
        """
        super_context = getattr(super(), 'get_context_data', None)
        if super_context and callable(super_context):
            context = super_context(**kwargs)
        else:
            context = {}

        context['widgets'] = {widget_type.__name__: {} for widget_type in
                              BaCa2ContextMixin.WIDGET_TYPES}

        request = getattr(self, 'request', None)
        if request:
            if request.user.is_authenticated:
                context['data_bs_theme'] = request.user.user_settings.theme
                context['display_navbar'] = True
                self.add_widget(context, NavBar(request))
            else:
                context['data_bs_theme'] = BaCa2ContextMixin.DEFAULT_THEME
                context['display_navbar'] = False
        else:
            raise Exception('No request object found. Remember that BaCa2ContextMixin should only '
                            'be used as a view mixin.')

        return context

    @staticmethod
    def add_widget(context: Dict[str, Any], widget: Widget) -> None:
        """
        Add a widget to the context dictionary. The widget is added to its corresponding widget
        type dictionary (in the `widgets` dictionary of the main context dict) under its name as a
        key.

        :param context: Context dictionary to which the widget is to be added.
        :type context: Dict[str, Any]

        :param widget: Widget to be added to the context dictionary.
        :type widget: Widget

        :raises WidgetException: If the widget type is not recognized or if it is unique and
            already exists in the context dictionary.
        """
        if isinstance(widget, NewCourseFormWidget):
            x = 10
        widget_type = BaCa2ContextMixin.get_type(type(widget))

        if not widget_type:
            raise BaCa2ContextMixin.WidgetException(f'Widget type not recognized: {widget_type}.')

        if (BaCa2ContextMixin.has_widget_type(context, widget_type) and
                widget_type in BaCa2ContextMixin.UNIQUE_WIDGETS):
            raise BaCa2ContextMixin.WidgetException(f'Widget of type {widget_type} already '
                                                    f'exists in the context dictionary.')

        if widget_type == SideNav:
            context['display_sidenav'] = True

        context['widgets'][widget_type.__name__][widget.name] = widget.get_context()

    @staticmethod
    def has_widget_type(context: Dict[str, Any], widget_type: Type[Widget]) -> bool:
        """
        Checks if the context dictionary contains at least one widget of the specified type.

        :param context: Context dictionary to check.
        :type context: Dict[str, Any]
        :param widget_type: Widget type to check for.
        :type widget_type: Type[Widget]

        :return: `True` if the context dictionary contains at least one widget of the specified
            type, `False` otherwise.
        :rtype: bool

        :raises WidgetException: If the widget type is not recognized.
        """
        if widget_type not in BaCa2ContextMixin.WIDGET_TYPES:
            widget_type = BaCa2ContextMixin.get_type(widget_type)
        if not widget_type:
            raise BaCa2ContextMixin.WidgetException(f'Widget type not recognized: {widget_type}.')
        if context['widgets'][widget_type.__name__]:
            return True
        return False

    @staticmethod
    def has_widget(context: Dict[str, Any], widget_type: Type[Widget], widget_name: str) -> bool:
        """
        Checks if the context dictionary contains a widget of the specified type and name.

        :param context: Context dictionary to check.
        :type context: Dict[str, Any]
        :param widget_type: Widget type to check for.
        :type widget_type: Type[Widget]
        :param widget_name: Widget name to check for.
        :type widget_name: str

        :return: `True` if the context dictionary contains a widget of the specified type and name,
            `False` otherwise.
        :rtype: bool

        :raises WidgetException: If the widget type is not recognized.
        """
        if widget_type not in BaCa2ContextMixin.WIDGET_TYPES:
            raise BaCa2ContextMixin.WidgetException(f'Widget type not recognized: {widget_type}.')
        if context['widgets'][widget_type.__name__].get(widget_name, None):
            return True
        return False

    @staticmethod
    def get_type(widget_cls: Type[Widget]) -> Type[Widget] | None:
        """
        Returns the type of given widget class if it is recognized, `None` otherwise.

        :param widget_cls: Widget class to check.
        :type widget_cls: Type[Widget]

        :return: Type of the widget class if recognized, `None` otherwise.
        :rtype: Type[Widget] | None
        """
        for widget_type in BaCa2ContextMixin.WIDGET_TYPES:
            if issubclass(widget_cls, widget_type):
                return widget_type
        return None


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


class BaCa2LoggedInView(LoginRequiredMixin, BaCa2ContextMixin, TemplateView):
    """
    Base view for all views which require the user to be logged in. Inherits from BaCa2ContextMixin
    providing a navbar widget and a preliminary setup for the context dictionary.
    """

    # Baca2LoggedInView is a base, abstract class and as such does not have a template. All
    # subclasses should provide their own template.
    template_name = None


class AdminView(BaCa2LoggedInView, UserPassesTestMixin):
    """
    Admin view for BaCa2 used to manage users, courses and packages. Can only be accessed by
    superusers.
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
        sidenav = SideNav('users', 'courses', 'packages')
        self.add_widget(context, sidenav)

        if not self.has_widget(context, FormWidget, 'create_course_form_widget'):
            self.add_widget(context, NewCourseFormWidget())

        self.add_widget(context, TableWidget(
            name='courses_table',
            model_cls=Course,
            access_mode='admin',
            create=True,
            details=True,
            edit=True,
            delete=True,
            select=True,
            cols=['id', 'name'],
            header={'name': 'Course Name'},
            default_order_col='name',
            refresh=False,
            paging=False
        ))

        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('form_name', None) == 'create_course_form':
            form = NewCourseForm(data=request.POST)

            if form.is_valid():
                Course.objects.create_course(
                    name=form.cleaned_data['name'],
                    short_name=form.cleaned_data.get('short_name', None),
                )
                return JsonResponse({'status': 'ok'})
            else:
                kwargs['new_course_form_widget'] = NewCourseFormWidget(form=form).get_context()
                return self.get(request, *args, **kwargs)
        else:
            return JsonResponse(
                {'status': 'error, unknown form name',
                 'form_name': request.POST.get('form_name', None)}
            )


class DashboardView(BaCa2LoggedInView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['display_navbar'] = True
        return context


class CoursesView(BaCa2LoggedInView):
    template_name = 'courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        table = TableWidget(model_cls=Course,
                            refresh=False,
                            paging=False)

        context['table'] = table.get_context()
        return context


class JsonView(LoginRequiredMixin, View):
    @staticmethod
    def get(request, *args, **kwargs):
        if kwargs['model_name'] == 'course':
            if kwargs['access_mode'] == 'user':
                return JsonResponse(
                    {'data': [course.get_data() for course in Course.objects.filter(
                        usercourse__user=request.user
                    )]}
                )
            elif kwargs['access_mode'] == 'admin':
                if request.user.is_superuser:
                    return JsonResponse(
                        {'data': [course.get_data() for course in Course.objects.all()]}
                    )
                else:
                    return JsonResponse({'status': 'error',
                                         'message': 'Access denied.'})

        return JsonResponse({'status': 'error',
                             'message': 'Model name not recognized.'})


class FieldValidationView(LoginRequiredMixin, View):
    class FieldClassException(Exception):
        pass

    @staticmethod
    def get(request, *args, **kwargs):
        field_cls_name = request.GET.get('field_cls', None)

        if not field_cls_name:
            raise FieldValidationView.FieldClassException('No field class name provided.')

        return JsonResponse(
            forms.base.get_field_validation_status(
                field_cls=field_cls_name,
                value=request.GET.get('value', ''),
                required=request.GET.get('required', False),
                min_length=request.GET.get('min_length', False))
        )


def change_theme(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            theme = request.POST.get('theme')
            request.user.user_settings.theme = theme
            request.user.user_settings.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})
