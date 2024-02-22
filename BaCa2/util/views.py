from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Type

import django.db.models
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from core.choices import BasicModelAction
from util import (
    add_kwargs_to_url,
    decode_url_to_dict,
    encode_dict_to_url,
    normalize_string_to_python
)
from util.models import model_cls
from util.responses import BaCa2JsonResponse, BaCa2ModelResponse
from widgets.base import Widget
from widgets.forms import FormWidget
from widgets.forms.fields.validation import get_field_validation_status
from widgets.listing import TableWidget
from widgets.navigation import NavBar, SideNav
from widgets.text_display import MarkupDisplayer, PDFDisplayer, TextDisplayer


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
    WIDGET_TYPES = [FormWidget,
                    NavBar,
                    SideNav,
                    TableWidget,
                    TextDisplayer,
                    MarkupDisplayer,
                    PDFDisplayer]
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

        context['display_sidenav'] = False

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

        if all((BaCa2ContextMixin.has_widget_type(context, widget_type),
                widget_type in BaCa2ContextMixin.UNIQUE_WIDGETS)):
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
                field_name=field_name,
                value=request.GET.get('value'),
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
        - :class:`widgets.forms.base.BaCa2ModelResponse`
    """

    class GetMode(Enum):
        """
        Enum containing all the available get modes for retrieving data from the view. The get mode
        defines which method is used to construct the QuerySet to be serialized and returned to the
        front-end.
        """
        #: Retrieve data for all model instances.
        ALL = 'all'
        #: Retrieve data for model instances matching the specified filter parameters.
        FILTER = 'filter'
        #: Retrieve data for model instances not matching the specified exclusion parameters.
        EXCLUDE = 'exclude'

    class ModelViewException(Exception):
        """
        Exception raised when an error not related to request arguments or requesting user
        permissions occurs while processing a GET or POST request.
        """
        pass

    #: Model class which the view manages. Should be set by inheriting classes.
    MODEL: model_cls = None

    # -------------------------------------- get methods --------------------------------------- #

    def get(self, request, *args, **kwargs) -> BaCa2ModelResponse:
        """
        Retrieves data for model instances in accordance with the specified get mode and query
        parameters.

        - Get mode 'ALL' - Retrieves data for all model instances.
        - Get mode 'FILTER' - Retrieves data for model instances matching the filter parameters
            specified in the url.
        - Get mode 'EXCLUDE' - Retrieves data for model instances not matching the exclusion
            parameters specified in the url.

        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: JSON response with the result of the action in the form of status and message
            string (and data if the action was successful).
        :rtype: :class:`BaCa2ModelResponse`
        :raises ModelViewException: If the model class managed by the view does not implement the
            `get_data` method needed to perform this action.

        See also:
            - :class:`BaCa2ModelView.GetMode`
            - :meth:`BaCa2ModelView.get_all`
            - :meth:`BaCa2ModelView.get_filtered`
            - :meth:`BaCa2ModelView.get_excluded`
        """
        get_data_method = getattr(self.MODEL, 'get_data')

        if not get_data_method or not callable(get_data_method):
            raise BaCa2ModelView.ModelViewException(
                f'Model class managed by the {self.__class__.__name__} view does not '
                f'implement the get_data method needed to perform this action.'
            )

        get_params = request.GET.dict()
        mode = get_params.get('mode')

        if not mode:
            return self.get_request_response(
                status=BaCa2JsonResponse.Status.INVALID,
                message=_('Failed to retrieve data for model instances due to missing target.')
            )

        if get_params.get('query_params'):
            query_params = decode_url_to_dict(get_params.get('query_params'))
        else:
            query_params = {}

        if get_params.get('serialize_kwargs'):
            serialize_kwargs = decode_url_to_dict(get_params.get('serialize_kwargs'))
        else:
            serialize_kwargs = {}

        if mode == self.GetMode.ALL.value:
            return self.get_all(query_params, serialize_kwargs, request, **kwargs)
        if mode == self.GetMode.FILTER.value:
            return self.get_filtered(query_params, serialize_kwargs, request, **kwargs)
        if mode == self.GetMode.EXCLUDE.value:
            return self.get_excluded(query_params, serialize_kwargs, request, **kwargs)

        return self.get_request_response(
            status=BaCa2JsonResponse.Status.INVALID,
            message=_('Failed to retrieve data for model instances due to invalid get mode '
                      'parameter.')
        )

    def get_all(self,
                query_params: dict,
                serialize_kwargs: dict,
                request,
                **kwargs) -> BaCa2ModelResponse:
        """
        :param query_params: Query parameters received by the view (should be empty, if not, the
            request is considered invalid).
        :type query_params: dict
        :param serialize_kwargs: Kwargs to pass to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: JSON response containing data for all model instances of the model class managed
            by the view (provided the user has permission to view them).
        :rtype: :class:`BaCa2ModelResponse`

        See also:
            - :meth:`BaCa2ModelView.check_get_all_permission`
            - :meth:`BaCa2ModelView.get`
            - :class:`BaCa2ModelResponse`
        """
        if len(query_params) > 0:
            return self.get_request_response(
                status=BaCa2JsonResponse.Status.INVALID,
                message=_('Get all retrieval mode does not accept query parameters.')
            )

        if not self.check_get_all_permission(request, **kwargs):
            return self.get_request_response(
                status=BaCa2JsonResponse.Status.IMPERMISSIBLE,
                message=_('Permission denied.')
            )

        return self.get_request_response(
            status=BaCa2JsonResponse.Status.SUCCESS,
            message=_('Successfully retrieved data for all model instances'),
            data=[instance.get_data(**serialize_kwargs) for instance in self.MODEL.objects.all()]
        )

    def get_filtered(self,
                     query_params: dict,
                     serialize_kwargs: dict,
                     request,
                     **kwargs) -> BaCa2ModelResponse:
        """
        :param query_params: Query parameters used to construct the filter for the retrieved query
            set.
        :type query_params: dict
        :param serialize_kwargs: Kwargs to pass to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: JSON response containing data for model instances matching the specified filter
            parameters (provided the user has permission to view them).
        :rtype: :class:`BaCa2ModelResponse`

        See also:
            - :meth:`BaCa2ModelView.check_get_filtered_permission`
            - :meth:`BaCa2ModelView.get`
            - :class:`BaCa2ModelResponse`
        """
        query_result = [obj for obj in self.MODEL.objects.filter(**query_params)]

        if not self.check_get_filtered_permission(query_params, query_result, request, **kwargs):
            return self.get_request_response(
                status=BaCa2JsonResponse.Status.IMPERMISSIBLE,
                message=_('Permission denied.')
            )

        return self.get_request_response(
            status=BaCa2JsonResponse.Status.SUCCESS,
            message=_('Successfully retrieved data for model instances matching the specified '
                      'filter parameters.'),
            data=[obj.get_data(**serialize_kwargs) for obj in query_result]
        )

    def get_excluded(self,
                     query_params: dict,
                     serialize_kwargs: dict,
                     request,
                     **kwargs) -> BaCa2ModelResponse:
        """
        :param query_params: Query parameters used to construct the exclude filter for the
            retrieved query set.
        :type query_params: dict
        :param serialize_kwargs: Kwargs to pass to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: JSON response containing data for model instances not matching the specified
            exclusion parameters (provided the user has permission to view them).
        :rtype: :class:`BaCa2ModelResponse`

        See also:
            - :meth:`BaCa2ModelView.check_get_excluded_permission`
            - :meth:`BaCa2ModelView.get`
            - :class:`BaCa2ModelResponse`
        """
        query_result = [obj for obj in self.MODEL.objects.exclude(**query_params)]

        if not self.check_get_excluded_permission(query_params, query_result, request, **kwargs):
            return self.get_request_response(
                status=BaCa2JsonResponse.Status.IMPERMISSIBLE,
                message=_('Permission denied.')
            )

        return self.get_request_response(
            status=BaCa2JsonResponse.Status.SUCCESS,
            message=_('Successfully retrieved data for model instances not matching the specified '
                      'exclusion parameters.'),
            data=[obj.get_data(**serialize_kwargs) for obj in query_result]
        )

    # --------------------------------- get permission checks ---------------------------------- #

    def check_get_all_permission(self, request, **kwargs) -> bool:
        """
        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: `True` if the user has the 'view' permission for the model class managed by the
            view, `False` otherwise.
        :rtype: bool

        See also:
            - :meth:`BaCa2ModelView.get_all`
        """
        return request.user.has_basic_model_permissions(self.MODEL, BasicModelAction.VIEW)

    @abstractmethod
    def check_get_filtered_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        """
        :param query_params: Query parameters used to filter the retrieved query set.
        :type query_params: dict
        :param query_result: Query set retrieved using the specified query parameters evaluated to a
            list.
        :type query_result: List[django.db.models.Model]
        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: `True` if the user has permission to view the model instances matching the
        :rtype: bool
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @abstractmethod
    def check_get_excluded_permission(self,
                                      query_params: dict,
                                      query_result: List[django.db.models.Model],
                                      request,
                                      **kwargs) -> bool:
        """
        :param query_params: Query parameters used to filter the retrieved query set.
        :type query_params: dict
        :param query_result: Query set retrieved using the specified query parameters evaluated to
            a list.
        :type query_result: List[django.db.models.Model]
        :param request: HTTP request object received by the view.
        :type request: HttpRequest
        :return: `True` if the user has permission to view the model instances not matching the
            specified exclusion parameters, `False` otherwise.
        :rtype: bool
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    # -------------------------------------- post methods -------------------------------------- #

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
    def handle_unknown_form(cls, request, **kwargs) -> BaCa2ModelResponse:
        """
        Generates a JSON response returned when the post request contains an unknown form name.

        :return: Error JSON response.
        :rtype: :class:`BaCa2ModelResponse`
        """
        return BaCa2ModelResponse(
            model=cls.MODEL,
            action=request.POST.get('action', ''),
            status=BaCa2JsonResponse.Status.ERROR,
            message=_(f'Unknown form: {request.POST.get("form_name")}')
        )

    # ----------------------------------- auxiliary methods ------------------------------------ #

    def get_request_response(self,
                             status: BaCa2JsonResponse.Status,
                             message: str,
                             data: list = None) -> BaCa2ModelResponse:
        """
        :param status: Status of the action.
        :type status: :class:`BaCa2JsonResponse.Status`
        :param message: Message describing the result of the action.
        :type message: str
        :param data: Data retrieved by the action (if any).
        :type data: list
        :return: JSON response with the result of the action in the form of status and message
            string (and data if the action was successful).
        :rtype: :class:`BaCa2ModelResponse`
        """
        return BaCa2ModelResponse(model=self.MODEL,
                                  action=BasicModelAction.VIEW,
                                  status=status,
                                  message=message,
                                  **{'data': data})

    @classmethod
    def _url(cls, **kwargs) -> str:
        """
        :return: Base url for the view. Used by :meth:`get_url` method.
        """
        return f'/{cls.MODEL._meta.app_label}/models/{cls.MODEL._meta.model_name}/'

    @classmethod
    def get_url(cls,
                mode: GetMode = GetMode.ALL,
                query_params: dict = None,
                serialize_kwargs: dict = None,
                **kwargs) -> str:
        """
        Returns a URL used to retrieve data from the view in accordance with the specified get mode
        and query parameters.

        :param mode: Get mode to use when retrieving data.
        :type mode: :class:`BaCa2ModelView.GetMode`
        :param query_params: Query parameters to use when retrieving data. Required when using
            :class:`BaCa2ModelView.GetMode.FILTER` or :class:`BaCa2ModelView.GetMode.EXCLUDE`.
        :type query_params: dict
        :param serialize_kwargs: Kwargs to pass to the serialization method of the model class
            instances retrieved by the view when the JSON response is generated.
        :type serialize_kwargs: dict
        :param kwargs: Additional keyword arguments to be added to the URL.
        :type kwargs: dict

        See also:
            - :class:`BaCa2ModelView.GetMode`
        """
        url = cls._url(**kwargs)

        if mode != cls.GetMode.ALL and query_params is None:
            raise BaCa2ModelView.ModelViewException(
                f'Query parameters must be specified when using {mode} get mode.'
            )

        if query_params or serialize_kwargs:
            url += '?'
        if query_params:
            url += encode_dict_to_url('query_params', query_params)
        if serialize_kwargs:
            url += f'&{encode_dict_to_url("serialize_kwargs", serialize_kwargs)}'

        url_kwargs = {'mode': mode.value} | kwargs
        return add_kwargs_to_url(url, url_kwargs)

    @classmethod
    def post_url(cls, **kwargs) -> str:
        """
        Returns a URL used to send a post request to the view.

        :param kwargs: Additional keyword arguments to be added to the URL.
        :type kwargs: dict
        """
        return f'{cls._url(**kwargs)}'
