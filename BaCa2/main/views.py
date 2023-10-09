from abc import ABC, abstractmethod
from typing import (Dict, Any, Type)

from django.views.generic.base import (TemplateView, RedirectView, View)
from django.contrib.auth.mixins import (LoginRequiredMixin, UserPassesTestMixin)
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import (JsonResponse, HttpResponseRedirect)
from django.http.request import HttpRequest
from django.urls import reverse_lazy

from main.models import Course
from widgets import forms
from widgets.base import Widget
from widgets.listing import TableWidget
from widgets.forms import FormWidget
from widgets.navigation import (NavBar, SideNav)
from widgets.forms.course import (NewCourseForm, NewCourseFormWidget)


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

    def get_context_data(self,
                         sidenav_included: bool = False,
                         sidenav_widget: SideNav = None,
                         **kwargs) -> Dict[str, Any]:
        """
        Returns a dictionary containing all the data required by the template to render the view.
        Calls on the `get_context_data` method of the other following ancestor (should there be
        one) in the MRO chain (As such, if this mixin precedes in the parent list of the view
        class an ancestor view whose context gathering is also necessary, it is enough to call on
        the `get_context_data` once through the super() method).

        :param sidenav_included: Whether the view contains a side navigation widget.
        :type sidenav_included: bool
        :param sidenav_widget: Side navigation widget to be added to the context dictionary if the
        view
            contains one.
        :type sidenav_widget: SideNav
        :param kwargs: Keyword arguments passed to the `get_context_data` method of the other
            following ancestor in the MRO chain (should there be one).
        :type kwargs: dict

        :return: A dictionary containing data required by the template to render the view.
        :rtype: Dict[str, Any]

        :raises Exception: If no request object is found or if the side navigation widget is
            required but not provided.
        """

        if sidenav_included and not sidenav_widget:
            raise BaCa2ContextMixin.WidgetException('Side navigation widget not provided despite '
                                                    'being required.')

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

        if sidenav_included:
            context['display_sidenav'] = True
            self.add_widget(context, sidenav_widget)

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
    template_name = 'admin.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        sidenav = SideNav('users', 'courses', 'packages')
        context = super().get_context_data(sidenav_included=True, sidenav_widget=sidenav, **kwargs)

        if not self.has_widget(context, FormWidget, 'new_course_form'):
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
        if request.POST.get('form_name', None) == 'new_course_form':
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
            forms.get_field_validation_status(
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
