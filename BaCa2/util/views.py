from abc import ABC, abstractmethod
from typing import Dict, Any, Type

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from BaCa2.choices import BasicPermissionType
from util import normalize_string_to_python
from util.models import model_cls
from widgets.base import Widget
from widgets.forms import FormWidget
from widgets.forms.base import BaCa2ModelFormResponse, BaCa2FormResponse
from widgets.forms.fields.validation import get_field_validation_status
from widgets.listing import TableWidget
from widgets.navigation import NavBar, SideNav


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

    #: List of all widget types used in BaCa2 views.
    WIDGET_TYPES = [FormWidget, NavBar, SideNav, TableWidget]
    #: List of all widgets which are unique (i.e. there can only be one instance of each widget type
    #: can exist in the context dictionary).
    UNIQUE_WIDGETS = [NavBar, SideNav]
    #: Default theme for users who are not logged in.
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


class BaCa2LoggedInView(LoginRequiredMixin, BaCa2ContextMixin, TemplateView):
    """
    Base view for all views which require the user to be logged in. Inherits from BaCa2ContextMixin
    providing a navbar widget and a preliminary setup for the context dictionary.
    """

    #: Baca2LoggedInView is a base, abstract class and as such does not have a template. All
    #: subclasses should provide their own template.
    template_name = None


class FieldValidationView(LoginRequiredMixin, View):
    """
    View used for live field validation. Its :meth:`get` method is called whenever the value of a
    field with live validation enabled changes. The method returns a JSON response containing the
    validation status of the field and any potential error messages to be displayed.

    See also:
        - :meth:`widgets.forms.fields.validation.get_field_validation_status`
        - :class:`widgets.forms.base.FormWidget`
    """

    class ValidationRequestException(Exception):
        """
        Exception raised when a validation request does not contain the required data.
        """
        pass

    @staticmethod
    def get(request, *args, **kwargs) -> JsonResponse:
        """
        Parses the request for the required data and returns a JSON response containing the
        validation status of the field and any potential error messages to be displayed.

        :return: JSON response with validation status and error messages.
        :rtype: JsonResponse
        :raises ValidationRequestException: If the request does not contain the required data.
        """
        form_cls_name = request.GET.get('formCls', None)
        field_name = request.GET.get('fieldName', None)

        if not form_cls_name or not field_name:
            raise FieldValidationView.ValidationRequestException(
                'Validation request does contain the required data.'
            )

        return JsonResponse(
            get_field_validation_status(
                request=request,
                form_cls=form_cls_name,
                field_name=normalize_string_to_python(field_name),
                value=normalize_string_to_python(request.GET.get('value')),
                min_length=normalize_string_to_python(request.GET.get('minLength', None))
            )
        )


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

    def test_view_permission(self, request, **kwargs) -> bool:
        """
        Checks if the user has permission to view data of the model class managed by the view.

        :return: `True` if the user has permission, `False` otherwise.
        :rtype: bool
        """
        return request.user.has_basic_model_permissions(self.MODEL, BasicPermissionType.VIEW)

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
