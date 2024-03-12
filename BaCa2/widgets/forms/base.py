from __future__ import annotations

import inspect
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Self

from django import forms
from django.forms.forms import DeclarativeFieldsMetaclass
from django.utils.translation import gettext_lazy as _

from core.choices import ModelAction
from util.models import model_cls
from util.responses import BaCa2JsonResponse, BaCa2ModelResponse
from widgets.base import Widget
from widgets.popups.forms import SubmitConfirmationPopup, SubmitFailurePopup, SubmitSuccessPopup

# --------------------------------------- baca2 form meta -------------------------------------- #

class BaCa2FormMeta(DeclarativeFieldsMetaclass, ABCMeta):
    """
    Metaclass for all forms inheriting from the :class:`BaCa2Form` base class. Used to handle the
    initialization and reconstruction of dynamic form instances from the session data. Reinforces
    the requirement for all non-abstract form classes to have a FORM_NAME attribute set and a
    request parameter in their __init__ method if they have custom init parameters.
    """

    class SessionDataError(Exception):
        """
        Exception raised when an error occurs while attempting to reconstruct a form from the
        session data.
        """
        pass

    def __init__(cls, name, bases, attrs) -> None:
        """
        Initializes the form class. Checks if the form class has appropriate attributes and init
        signature.

        :raises ValueError: If the form class is not abstract and does not have a FORM_NAME
            attribute set, if a request parameter is not present in its __init__ method when it has
            custom init parameters, or if it does not have a **kwargs parameter in its __init__
        """
        super().__init__(name, bases, attrs)

        if not issubclass(cls, ABC) and not hasattr(cls, 'FORM_NAME'):
            raise ValueError('All non-abstract form classes must have a FORM_NAME attribute set to '
                             'be used with the BaCa2FormMeta metaclass.')

        signature = inspect.signature(cls.__init__)
        param_names = list(signature.parameters.keys())

        if 'kwargs' not in param_names:
            raise ValueError('BaCa2Form classes must have a **kwargs parameter in their __init__ '
                             'method to enable the form to be reconstructed with bound data from a '
                             'post request.')

        non_default_params = [param for param in param_names if param
                              not in ['self', 'args', 'kwargs', 'form_instance_id', 'request']]

        if non_default_params and 'request' not in param_names:
            raise ValueError('BaCa2Form classes with custom init parameters must have a request '
                             'parameter in their __init__ method to enable the form to be saved in '
                             'the session and used to recreate the form upon receiving a post or '
                             'validation request.')

    def __call__(cls, *args, **kwargs) -> Self:
        """
        Initializes a new form instance. If the form is instantiated with custom init parameters,
        saves the parameters to the session and returns the form instance. If the form is not
        instantiated with custom init parameters, returns the form instance as usual.

        :raises BaCa2FormMeta.SessionDataError: If the form is instantiated with custom init
            parameters and no request object is passed along with them.
        """
        if not args and not kwargs:
            return super().__call__()

        signature = inspect.signature(cls.__init__)
        param_names = list(signature.parameters.keys())
        named_args = dict(zip(param_names[1:], args))
        named_args.update(kwargs)
        request = named_args.pop('request', None)
        name = getattr(cls, 'FORM_NAME', None)

        if not request:
            raise BaCa2FormMeta.SessionDataError(
                'If a BaCa2Form is instantiated with custom init parameters, a request object must '
                'be passed along with them so that the parameters can be saved in the session and '
                'used to recreate the form upon receiving a post or validation request.'
            )

        if len(named_args) == 0:
            return cls.reconstruct_from_session(request)

        request.session.setdefault('form_init_params', {})
        form_init_params = request.session.get('form_init_params')
        form_init_params.setdefault(name, {})
        form_init_params = form_init_params.get(name)

        form_instance = super().__call__(*args, **kwargs)
        instance_id = form_instance.instance_id
        form_init_params[instance_id] = named_args

        request.session.save()

        return form_instance

    def reconstruct_from_session(cls, request) -> Self:
        """
        Reconstructs a form instance from the session data based on a request object.

        :raises BaCa2FormMeta.SessionDataError: If the form instance ID is not found in the request
            or no init parameters are found in the session for the form with the specified name and
            instance ID.
        """
        name = getattr(cls, 'FORM_NAME', None)
        instance_id = request.POST.get('form_instance_id')

        if not instance_id:
            instance_id = request.GET.get('form_instance_id')

        if not instance_id:
            raise BaCa2FormMeta.SessionDataError('No form instance ID found in the request.')

        init_params = request.session.get('form_init_params', {}).get(name, {}).get(instance_id)

        if not init_params:
            raise BaCa2FormMeta.SessionDataError('No init parameters found in the session for the '
                                                 'form with specified name and instance ID.')

        init_params['data'] = request.POST
        init_params['files'] = request.FILES
        init_params['request'] = request

        return super().__call__(**init_params)

    def reconstruct(cls, request) -> Self:
        """
        Attempts to reconstruct a form instance from the session data based on a request object. If
        the reconstruction fails, returns a new form instance based on the request's POST data.
        """
        try:
            return cls.reconstruct_from_session(request)
        except BaCa2FormMeta.SessionDataError:
            return super().__call__(data=request.POST, files=request.FILES)


class BaCa2ModelFormMeta(BaCa2FormMeta):
    """
    Metaclass for all forms inheriting from the :class:`BaCa2ModelForm` base class. Used to set the
    FORM_NAME attribute based on the ACTION attribute during the initialization of the form class.
    """

    def __init__(cls, name, bases, attrs) -> None:
        """
        Initializes the form class. Sets the FORM_NAME attribute based on the ACTION attribute if
        present.
        """
        super().__init__(name, bases, attrs)

        action = getattr(cls, 'ACTION', None)

        if action:
            cls.FORM_NAME = f'{action.label}_form'


# -------------------------------------- base form classes ------------------------------------- #

class BaCa2Form(forms.Form, ABC, metaclass=BaCa2FormMeta):
    """
    Base form for all forms in the BaCa2 system. Contains shared, hidden fields common to all forms.

    See Also:
        :class:`BaCa2ModelForm`
        :class:`FormWidget`
    """

    #: Name of the form. Used to identify the form class when receiving a POST request and to
    #: reconstruct the form from (and save its init parameters to) the session.
    FORM_NAME = None

    form_name = forms.CharField(
        label=_('Form name'),
        max_length=100,
        widget=forms.HiddenInput(),
        required=True,
        initial='form'
    )
    form_instance_id = forms.IntegerField(
        label=_('Form instance'),
        widget=forms.HiddenInput(),
        required=True
    )
    action = forms.CharField(
        label=_('Action'),
        max_length=100,
        widget=forms.HiddenInput(),
        initial='',
    )

    def __init__(self, *, form_instance_id: int = 0, request=None, **kwargs) -> None:
        """
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the parent class constructor.
        :type kwargs: dict
        """

        super().__init__(**kwargs)
        self.fields['form_name'].initial = self.FORM_NAME
        self.instance_id = form_instance_id
        self.fields['form_instance_id'].initial = form_instance_id
        self.request = request

    def __repr__(self) -> str:
        """
        :return: String representation of the form instance containing information about the form's
            bound status, validity and fields.
        :rtype: str
        """
        if self.errors is None:
            is_valid = 'Unknown'
        else:
            is_valid = self.is_bound and not self.errors
        return '<%(cls)s bound=%(bound)s, valid=%(valid)s, fields=(%(fields)s)>' % {
            'cls': self.__class__.__name__,
            'bound': self.is_bound,
            'valid': is_valid,
            'fields': ';'.join(self.fields),
        }

    def fill_with_data(self, data: Dict[str, str]) -> Self:
        """
        Fills the form with the specified data.

        :param data: Dictionary containing the data to be used to fill the form.
        :type data: dict
        """
        for field in self.fields:
            if field in data.keys():
                self.fields[field].initial = data[field]
        return self


class BaCa2ModelForm(BaCa2Form, ABC, metaclass=BaCa2ModelFormMeta):
    """
    Base class for all forms in the BaCa2 app which are used to create, delete or modify model
    objects.

    See Also:
        :class:`BaCa2Form`
    """

    #: Model class which instances are affected by the form.
    MODEL: model_cls = None
    #: Action which should be performed using the form data.
    ACTION: ModelAction = None

    def __init__(self, *, form_instance_id: int = 0, request=None, **kwargs):
        """
        :param form_instance_id: ID of the form instance. Used to identify the form instance when
            saving its init parameters to the session and to reconstruct the form from the session.
            Defaults to 0. Should be set to a unique value when creating a new form instance within
            a single view with multiple instances of the same form class.
        :type form_instance_id: int
        :param request: HTTP request object received by the view the form is rendered in. Should be
            passed to the constructor if the form is instantiated with custom init parameters.
        :type request: HttpRequest
        :param kwargs: Additional keyword arguments to be passed to the parent class constructor.
        :type kwargs: dict
        """
        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)
        self.fields['action'].initial = self.ACTION.value

    @classmethod
    def handle_post_request(cls, request) -> BaCa2ModelResponse:
        """
        Handles the POST request received by the view this form's data was posted to. Based on the
        user's permissions and the validity of the form data, returns a JSON response containing
        information about the status of the request and a message accompanying it, along with any
        additional data needed to process the response.

        :param request: Request object.
        :type request: HttpRequest
        :return: JSON response to the request.
        :rtype: :class:`BaCa2ModelResponse`
        """
        if not cls.is_permissible(request):
            return BaCa2ModelResponse(
                model=cls.MODEL,
                action=cls.ACTION,
                status=BaCa2JsonResponse.Status.IMPERMISSIBLE,
                **cls.handle_impermissible_request(request)
            )

        form = cls.reconstruct(request)

        if form.is_valid():
            try:
                return BaCa2ModelResponse(
                    model=cls.MODEL,
                    action=cls.ACTION,
                    status=BaCa2JsonResponse.Status.SUCCESS,
                    **cls.handle_valid_request(request)
                )
            except Exception as e:
                messages = [arg for arg in e.args if arg]

                if not messages:
                    messages = [str(e)]

                return BaCa2ModelResponse(
                    model=cls.MODEL,
                    action=cls.ACTION,
                    status=BaCa2JsonResponse.Status.ERROR,
                    **cls.handle_error(request, e) | {'errors': messages}
                )

        validation_errors = form.errors

        return BaCa2ModelResponse(
            model=cls.MODEL,
            action=cls.ACTION,
            status=BaCa2JsonResponse.Status.INVALID,
            **cls.handle_invalid_request(request, validation_errors) | {'errors': validation_errors}
        )

    @classmethod
    @abstractmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible and the form data is valid.

        :param request: Request object.
        :type request: HttpRequest
        :return: Dictionary containing a success message and any additional data to be included in
            the response.
        :rtype: Dict[str, Any]
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible but the form data is invalid.

        :param request: Request object.
        :type request: HttpRequest
        :param errors: Dictionary containing information about the errors found in the form data.
        :type errors: dict
        :return: Dictionary containing a failure message. If the form widget has a submit failure
            popup, the message will be displayed in the popup followed by information about the
            errors found in the form data.
        :rtype: Dict[str, Any]
        """
        return {'message': _('Invalid form data. Please correct the following errors:')}

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is impermissible.

        :param request: Request object.
        :type request: HttpRequest
        :return: Dictionary containing a failure message.
        :rtype: Dict[str, Any]
        """
        return {'message': _('Request failed due to insufficient permissions.')}

    @classmethod
    def handle_error(cls, request, error: Exception) -> Dict[str, Any]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        resulted in an error unrelated to form validation or the user's permissions.

        :param request: Request object.
        :type request: HttpRequest
        :param error: Error which occurred while processing the request.
        :type error: Exception
        :return: Dictionary containing a failure message. If the form widget has a submit failure
            popup, the message will be displayed in the popup followed by information about the
            error which occurred.
        :rtype: Dict[str, Any]
        """
        return {'message': _('Following error occurred while processing the request:')}

    @classmethod
    def is_permissible(cls, request) -> bool:
        """
        Checks whether the user has the permission to perform the action specified by the form.

        :param request: Request object.
        :type request: HttpRequest

        :return: `True` if the user has the permission to perform the action specified by the form,
            `False` otherwise.
        :rtype: bool
        """
        return request.user.has_permission(cls.ACTION.label)


# ----------------------------------------- form widget ---------------------------------------- #

class FormWidget(Widget):
    """
    Base :class:`Widget` class for all form widgets. Responsible for generating the context
    dictionary needed to render a form in accordance with the specified parameters.

    Templates used for rendering forms are located in the `BaCa2/templates/widget_templates/forms`
    directory. The default template used for rendering forms is `default.html`. Any custom form
    templates should extend the `base.html` template.

    See Also:
        - :class:`FormPostTarget`
        - :class:`FormElementGroup`
        - :class:`SubmitConfirmationPopup`
        - :class:`FormSuccessPopup`
        - :class:`FormFailurePopup`
    """

    def __init__(self,
                 *,
                 request,
                 form: forms.Form,
                 post_target_url: str = '',
                 name: str = '',
                 button_text: str = None,
                 refresh_button: bool = True,
                 display_non_field_validation: bool = True,
                 display_field_errors: bool = True,
                 floating_labels: bool = True,
                 element_groups: FormElementGroup | List[FormElementGroup] = None,
                 toggleable_fields: List[str] = None,
                 toggleable_params: Dict[str, Dict[str, str]] = None,
                 live_validation: bool = True,
                 form_observer: FormObserver = None,
                 submit_confirmation_popup: SubmitConfirmationPopup = None,
                 submit_success_popup: SubmitSuccessPopup = None,
                 submit_failure_popup: SubmitFailurePopup = None) -> None:
        """
        :param request: HTTP request object received by the view this form widget is rendered in.
        :type request: HttpRequest
        :param form: Form to be rendered.
        :type form: forms.Form
        :param post_target_url: Target URL for the form's POST request. If no target is specified,
            the form will be posted to the same URL as the page it is rendered on.
        :type post_target_url: str
        :param name: Name of the widget. If no name is specified, the name of the form will be used
            to generate the widget name.
        :type name: str
        :param button_text: Text displayed on the submit button.
        :type button_text: str
        :param refresh_button: Determines whether the form should have a refresh button.
        :type refresh_button: bool
        :param display_non_field_validation: Determines whether non-field validation errors should
            be displayed.
        :type display_non_field_validation: bool
        :param display_field_errors: Determines whether field errors should be displayed.
        :type display_field_errors: bool
        :param floating_labels: Determines whether the form should use floating labels.
        :type floating_labels: bool
        :param element_groups: Groups of form elements. Used to create more complex form layouts or
            assign certain behaviors to groups of fields.
        :type element_groups: :class:`FormElementGroup` | List[:class:`FormElementGroup`]
        :param toggleable_fields: List of names of fields which should be rendered as toggleable.
        :type toggleable_fields: List[str]
        :param toggleable_params: Parameters for toggleable fields. Each field name should be a key
            in the dictionary. The value of each key should be a dictionary containing the
            'button_text_on' and 'button_text_off' keys. The values of these keys will be used as
            the text displayed on the toggle button when the field is enabled and disabled
            respectively.
        :type toggleable_params: Dict[str, Dict[str, str]]
        :param live_validation: Determines whether the form should use live validation. Password
            fields will always be excluded from live validation.
        :type live_validation: bool
        :param form_observer: Determines the rendering and behavior of the form observer. If no
            observer is specified, no observer will be rendered.
        :type form_observer: :class:`FormObserver`
        :param submit_confirmation_popup: Determines the rendering of the confirmation popup shown
            before submitting the form. If no popup is specified, no popup will be shown and the
            form will be submitted immediately upon clicking the submit button.
        :type submit_confirmation_popup: :class:`SubmitConfirmationPopup`
        :param submit_success_popup: Determines the rendering of the success popup shown after
            submitting the form and receiving a successful response. If no popup is specified, no
            popup will be shown.
        :type submit_success_popup: :class:`SubmitSuccessPopup`
        :param submit_failure_popup: Determines the rendering of the failure popup shown after
            submitting the form and receiving an unsuccessful response. If no popup is specified, no
            popup will be shown.
        :type submit_failure_popup: :class:`SubmitFailurePopup`
        :raises Widget.WidgetParameterError: If no name is specified and the form passed to the
            widget does not have a name. If submit success popup or submit failure popup is
            specified without the other.
        """
        if button_text is None:
            button_text = _('Submit')
        if submit_success_popup is None:
            submit_success_popup = SubmitSuccessPopup()
        if submit_failure_popup is None:
            submit_failure_popup = SubmitFailurePopup()

        if not name:
            form_name = getattr(form, 'form_name', False)
            if form_name:
                name = f'{form_name}_widget'
            else:
                raise Widget.WidgetParameterError(
                    'Cannot create form widget for an unnamed form without specifying the widget '
                    'name.'
                )

        if (submit_success_popup is None) ^ (submit_failure_popup is None):
            raise Widget.WidgetParameterError(
                'Both submit success popup and submit failure popup must be specified or neither.'
            )

        super().__init__(name=name, request=request)
        self.form = form
        self.form_cls = form.__class__.__name__
        self.post_url = post_target_url
        self.button_text = button_text
        self.refresh_button = refresh_button
        self.display_non_field_validation = display_non_field_validation
        self.display_field_errors = display_field_errors
        self.floating_labels = floating_labels
        self.live_validation = live_validation
        self.show_response_popups = False

        if form_observer:
            form_observer.name = f'{self.name}_observer'
            form_observer = form_observer.get_context()
        self.form_observer = form_observer

        if submit_confirmation_popup:
            submit_confirmation_popup.name = f'{self.name}_confirmation_popup'
            submit_confirmation_popup.request = request
            submit_confirmation_popup = submit_confirmation_popup.get_context()
        self.submit_confirmation_popup = submit_confirmation_popup

        if submit_success_popup:
            self.show_response_popups = True
            submit_success_popup.name = f'{self.name}_success_popup'
            submit_success_popup.request = request
            submit_success_popup = submit_success_popup.get_context()
        self.submit_success_popup = submit_success_popup

        if submit_failure_popup:
            submit_failure_popup.name = f'{self.name}_failure_popup'
            submit_failure_popup.request = request
            submit_failure_popup = submit_failure_popup.get_context()
        self.submit_failure_popup = submit_failure_popup

        if not element_groups:
            element_groups = []
        if not isinstance(element_groups, list):
            element_groups = [element_groups]
        elements = []
        included_fields = {field.name: False for field in form}

        for field in form:
            if included_fields[field.name]:
                continue

            for group in element_groups:
                group.request = request
                if group.field_in_group(field.name):
                    elements.append(group)
                    included_fields.update({field_name: True for field_name in group.fields()})
                    break

            if not included_fields[field.name]:
                elements.append(field.name)
                included_fields[field.name] = True

        self.elements = FormElementGroup(elements=elements, name='form_elements')

        if not toggleable_fields:
            toggleable_fields = []
        self.toggleable_fields = toggleable_fields

        if not toggleable_params:
            toggleable_params = {}
        self.toggleable_params = toggleable_params

        for field in toggleable_fields:
            if field not in toggleable_params.keys():
                toggleable_params[field] = {}
        for params in toggleable_params.values():
            if 'button_text_on' not in params.keys():
                params['button_text_on'] = _('Generate automatically')
            if 'button_text_off' not in params.keys():
                params['button_text_off'] = _('Enter manually')

        self.field_classes = {
            field_name: self.form.fields[field_name].__class__.__name__
            for field_name in self.form.fields.keys()
        }

        self.field_required = {
            field_name: self.form.fields[field_name].required
            for field_name in self.form.fields.keys()
        }

        self.field_min_length = {}
        for field_name in self.form.fields.keys():
            if hasattr(self.form.fields[field_name], 'min_length'):
                self.field_min_length[field_name] = self.form.fields[field_name].min_length
            else:
                self.field_min_length[field_name] = False

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'form': self.form,
            'form_cls': self.form_cls,
            'post_url': self.post_url,
            'elements': self.elements,
            'button_text': self.button_text,
            'refresh_button': self.refresh_button,
            'display_non_field_errors': self.display_non_field_validation,
            'display_field_errors': self.display_field_errors,
            'floating_labels': self.floating_labels,
            'toggleable_fields': self.toggleable_fields,
            'toggleable_params': self.toggleable_params,
            'field_classes': self.field_classes,
            'field_required': self.field_required,
            'field_min_length': self.field_min_length,
            'live_validation': self.live_validation,
            'form_observer': self.form_observer,
            'submit_confirmation_popup': self.submit_confirmation_popup,
            'show_response_popups': self.show_response_popups,
            'submit_failure_popup': self.submit_failure_popup,
            'submit_success_popup': self.submit_success_popup,
        }


# -------------------------------------- form element group ------------------------------------ #

class FormElementGroup(Widget):
    """
    Class used to group form elements together. Used to dictate the layout or assign certain
    behaviors to groups of fields. More complex form layouts can be created by nesting multiple
    form element groups.

    See Also:
        - :class:`FormWidget`
    """

    class FormElementsLayout(Enum):
        """
        Enum used to specify the layout of form elements in a group.
        """
        #: Form elements will be displayed in a single row.
        HORIZONTAL = 'horizontal'
        #: Form elements will be displayed in a single column.
        VERTICAL = 'vertical'

    def __init__(self,
                 *,
                 elements: List[str | FormElementGroup],
                 name: str,
                 title: str = '',
                 display_title: bool = False,
                 request=None,
                 layout: FormElementsLayout = FormElementsLayout.VERTICAL,
                 toggleable: bool = False,
                 toggleable_params: Dict[str, str] = None,
                 frame: bool = False) -> None:
        """
        :param elements: Form elements to be included in the group, specified as a list of field
            names or other form element groups.
        :type elements: List[str | :class:`FormElementGroup`]
        :param name: Name of the group.
        :type name: str
        :param title: Title of the group. If no title is specified, the group will not have a title.
        :type title: str
        :param display_title: Determines whether the title should be displayed above the group.
        :type display_title: bool
        :param request: HTTP request object received by the parent form widget.
        :type request: HttpRequest
        :param layout: Layout of the form elements in the group.
        :type layout: :class:`FormElementGroup.FormElementsLayout`
        :param toggleable: Determines whether the group should be toggleable.
        :type toggleable: bool
        :param toggleable_params: Parameters for the toggleable group. Should contain the
            'button_text_on' and 'button_text_off' keys. The values of these keys will be used as
            the text displayed on the toggle button when the group is enabled and disabled
            respectively. If no parameters are specified, default values will be used.
        :type toggleable_params: Dict[str, str]
        :param frame: Determines whether the group should be displayed in a frame.
        :type frame: bool
        :raises ValueError: If no title is specified and the display_title parameter is set to True.
        """
        super().__init__(name=name, request=request)

        if not title and display_title:
            raise ValueError('A title must be specified if the display_title parameter is set '
                             'to True.')

        self.title = title
        self.display_title = display_title
        self.elements = elements
        self.toggleable = toggleable
        self.layout = layout.value
        self.frame = frame

        if not toggleable_params:
            toggleable_params = {}
        self.toggleable_params = toggleable_params

        if toggleable:
            if 'button_text_on' not in toggleable_params.keys():
                toggleable_params['button_text_on'] = _('Generate automatically')
            if 'button_text_off' not in toggleable_params.keys():
                toggleable_params['button_text_off'] = _('Enter manually')

    def field_in_group(self, field_name: str) -> bool:
        """
        Checks whether the specified field is included in the group.

        :param field_name: Name of the field to check.
        :type field_name: str
        :return: `True` if the field is included in the group, `False` otherwise.
        :rtype: bool
        """
        if field_name in self.elements:
            return True
        for element in self.elements:
            if isinstance(element, FormElementGroup):
                if element.field_in_group(field_name):
                    return True
        return False

    def fields(self) -> List[str]:
        """
        Returns a list containing the names of all fields included in the group.

        :return: List of field names.
        :rtype: List[str]
        """
        fields = []
        for element in self.elements:
            if isinstance(element, FormElementGroup):
                fields.extend(element.fields())
            else:
                fields.append(element)
        return fields

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'display_title': self.display_title,
            'elements': self.elements,
            'layout': self.layout,
            'toggleable': self.toggleable,
            'toggleable_params': self.toggleable_params,
            'frame': self.frame
        }


# ------------------------------------ form observer widget ------------------------------------ #

class FormObserver(Widget):
    class Position(Enum):
        TOP = 'top'
        BOTTOM = 'bottom'

    def __init__(self, *,
                 name: str = '',
                 title: str = '',
                 placeholder_text: str = '',
                 display_element_group_titles: bool = True,
                 tabs: List[FormObserverTab] = None,
                 position: FormObserver.Position = None) -> None:
        super().__init__(name=name)

        if not title:
            title = _('Summary of changes')
        self.title = title

        if not placeholder_text:
            placeholder_text = _('No changes made')
        self.placeholder_text = placeholder_text

        self.display_element_group_titles = display_element_group_titles

        if not tabs:
            tabs = []
        self.tabs = tabs

        if not position:
            position = FormObserver.Position.TOP
        self.position = position.value

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'placeholder_text': self.placeholder_text,
            'element_group_titles': self.display_element_group_titles,
            'position': self.position,
            'tabs': [tab.get_context() for tab in self.tabs]
        }


class FormObserverTab:
    def __init__(self, *, name: str, title: str = '', fields: List[str]) -> None:
        if not fields:
            raise ValueError('At least one field must be specified for the tab.')

        self.name = name
        self.fields = fields

        if not title:
            title = name
        self.title = title

    def get_context(self) -> Dict[str, str]:
        return {
            'name': self.name,
            'title': self.title,
            'fields': ' '.join(self.fields)
        }
