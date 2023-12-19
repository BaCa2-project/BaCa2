from __future__ import annotations

from typing import (Dict, List, Any)
from enum import Enum
from abc import ABC, abstractmethod

from django import forms
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from widgets.popups import FormConfirmationPopup
from util.models import model_cls
from util.models_registry import ModelsRegistry
from BaCa2.choices import ModelAction
from main.models import Course


class FormWidget(Widget):
    """
    Base :class:`widgets.base.Widget` for all forms. Responsible for generating the context
    dictionary necessary for rendering a form in accordance with the specified parameters.

    Templates used for rendering forms are located in the `BaCa2/templates/widget_templates/forms`
    directory. The default template used for rendering forms is `default.html`. Any custom form
    templates should extend the `base.html` template.

    See Also:
        - :class:`FormPostTarget`
        - :class:`FormElementGroup`
        - :class:`FormConfirmationPopup`
        - :class:`FormSuccessPopup`
    """

    def __init__(self,
                 *,
                 form: forms.Form,
                 post_target: FormPostTarget | str = None,
                 name: str = '',
                 button_text: str = _('Submit'),
                 refresh_button: bool = True,
                 display_non_field_validation: bool = True,
                 display_field_errors: bool = True,
                 floating_labels: bool = True,
                 element_groups: FormElementGroup | List[FormElementGroup] = None,
                 toggleable_fields: List[str] = None,
                 toggleable_params: Dict[str, Dict[str, str]] = None,
                 live_validation: bool = True,
                 submit_confirmation_popup: FormConfirmationPopup = None,
                 submit_success_popup: bool = True) -> None:
        """
        :param form: Form to be rendered.
        :type form: forms.Form
        :param post_target: Target URL for the form's POST request. If no target is specified, the
            form will be posted to the same URL as the page it is rendered on.
        :type post_target: :class:`FormPostTarget` | str
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
        :param submit_confirmation_popup: Determines the rendering of the confirmation popup shown
            before submitting the form. If no popup is specified, no popup will be shown and the
            form will be submitted immediately upon clicking the submit button.
        :type submit_confirmation_popup: :class:`widgets.popups.FormConfirmationPopup`
        :param submit_success_popup: Determines whether the form should display a popup upon
            successful submission.
        :type submit_success_popup: bool
        :raises Widget.WidgetParameterError: If no name is specified and the form passed to the
            widget does not have a name.
        """
        if not name:
            form_name = getattr(form, 'form_name', False)
            if form_name:
                name = f'{form_name}_widget'
            else:
                raise Widget.WidgetParameterError(
                    'Cannot create form widget for an unnamed form without specifying the widget '
                    'name.'
                )

        super().__init__(name)
        self.form = form
        self.form_cls = form.__class__.__name__
        self.button_text = button_text
        self.refresh_button = refresh_button
        self.display_non_field_validation = display_non_field_validation
        self.display_field_errors = display_field_errors
        self.floating_labels = floating_labels
        self.live_validation = live_validation
        self.submit_success_popup = submit_success_popup
        self.submit_confirmation_popup = submit_confirmation_popup

        if submit_confirmation_popup:
            self.submit_confirmation_popup.name = f'{self.name}_confirmation_popup'

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
                if group.field_in_group(field.name):
                    elements.append(group)
                    included_fields.update({field_name: True for field_name in group.fields()})
                    break

            if not included_fields[field.name]:
                elements.append(field.name)
                included_fields[field.name] = True

        self.elements = FormElementGroup(elements, 'form_elements')

        if not post_target:
            post_target = ''
        if isinstance(post_target, FormPostTarget):
            post_target = post_target.get_post_url()
        self.post_url = post_target

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

    def get_context(self) -> dict:
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
            'submit_confirmation_popup': self.submit_confirmation_popup.get_context(),
            'submit_success_popup': self.submit_success_popup
        }


class FormPostTarget(ABC):
    @abstractmethod
    def get_post_url(self) -> str:
        raise NotImplementedError('This method has to be implemented by inheriting classes.')


class ModelFormPostTarget(FormPostTarget):
    def __init__(self, model: model_cls) -> None:
        self.model = model

    def get_post_url(self) -> str:
        return f'/{self.model._meta.app_label}/models/{self.model._meta.model_name}'


class CourseModelFormPostTarget(ModelFormPostTarget):
    def __init__(self, model: model_cls, course: str | int | Course) -> None:
        if not isinstance(course, str):
            course = ModelsRegistry.get_course(course).short_name
        self.course = course
        super().__init__(model)

    def get_post_url(self) -> str:
        return f'course/{self.course}/models/{self.model._meta.model_name}'


class FormElementGroup(Widget):
    class FormElementsLayout(Enum):
        HORIZONTAL = 'horizontal'
        VERTICAL = 'vertical'

    def __init__(self,
                 elements: List[str | FormElementGroup],
                 name: str,
                 layout: FormElementsLayout = FormElementsLayout.VERTICAL,
                 toggleable: bool = False,
                 toggleable_params: Dict[str, str] = None,
                 frame: bool = False) -> None:
        super().__init__(name)
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
        if field_name in self.elements:
            return True
        for element in self.elements:
            if isinstance(element, FormElementGroup):
                if element.field_in_group(field_name):
                    return True
        return False

    def fields(self) -> List[str]:
        fields = []
        for element in self.elements:
            if isinstance(element, FormElementGroup):
                fields.extend(element.fields())
            else:
                fields.append(element)
        return fields

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'elements': self.elements,
            'layout': self.layout,
            'toggleable': self.toggleable,
            'toggleable_params': self.toggleable_params,
            'frame': self.frame
        }


class FormSuccessPopup(Widget):
    """
    :class:`widgets.base.Widget` used to render a popup displayed upon successful submission of a
    form.

    See Also:
        - :class:`FormWidget`
        - :class:`FormConfirmationPopup`
    """
    def __init__(self,
                 title: str,
                 description: str,
                 button_text: str = _('OK')) -> None:
        super().__init__('')
        self.title = title
        self.description = description
        self.button_text = button_text

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'description': self.description,
            'button_text': self.button_text
        }


class BaCa2FormResponse(JsonResponse):
    """
    Base class for all JSON responses returned as a result of an AJAX post request sent by a form
    widget. Contains basic fields required to handle the response along with predefined values
    for the status field.

    See Also:
        :class:`BaCa2Form`
        :class:`FormWidget`
    """

    class Status(Enum):
        """
        Enum used to indicate the possible outcomes of an AJAX post request sent by a form widget.
        Its values are used to determine the event triggered by the submit handling script upon
        receiving the response.
        """
        #: Indicates that the request was successful.
        SUCCESS = 'success'
        #: Indicates that the request was unsuccessful due to invalid form data.
        INVALID = 'invalid'
        #: Indicates that the request was unsuccessful due to the user not having the permission to
        #: perform the action specified by the form.
        IMPERMISSIBLE = 'impermissible'
        #: Indicates that the request was unsuccessful due to an error not related to form
        #: validation or the user's permissions.
        ERROR = 'error'

    def __init__(self, status: Status, message: str = '', **kwargs: dict) -> None:
        """
        :param status: Status of the response.
        :type status: :class:`BaCa2FormResponse.Status`
        :param message: Message accompanying the response.
        :type message: str
        :param kwargs: Additional fields to be included in the response.
        :type kwargs: dict
        """
        super().__init__({'status': status.value, 'message': message} | kwargs)


class BaCa2Form(forms.Form):
    """
    Base form for all forms in the BaCa2 system. Contains shared, hidden fields common to all forms.

    See Also:
        :class:`BaCa2ModelForm`
        :class:`FormWidget`
    """

    #: Form name used to identify the form for views which may receive post data from more than one
    # form.
    form_name = forms.CharField(
        label=_('Form name'),
        max_length=100,
        widget=forms.HiddenInput(),
        required=True,
        initial='form'
    )
    #: Informs the view receiving the post data about the action which should be performed using it.
    action = forms.CharField(
        label=_('Action'),
        max_length=100,
        widget=forms.HiddenInput(),
        initial='',
    )


class BaCa2ModelFormResponse(BaCa2FormResponse):
    """
    Base class for all JSON responses returned as a result of an AJAX post request sent by a model
    form.

    See Also:
        :class:`BaCa2ModelForm`
        :class:`BaCa2FormResponse`
    """

    def __init__(self,
                 model: model_cls,
                 action: ModelAction,
                 status: BaCa2FormResponse.Status,
                 message: str = '',
                 **kwargs: dict) -> None:
        """
        :param status: Status of the response.
        :type status: :class:`BaCa2FormResponse.Status`
        :param message: Message accompanying the response. If no message is provided, a default
            message will be generated based on the status of the response, the model and the action
            performed.
        :type message: str
        :param kwargs: Additional fields to be included in the response.
        :type kwargs: dict
        """
        if not message:
            message = self.generate_response_message(status, model, action)
        super().__init__(status, message, **kwargs)

    @staticmethod
    def generate_response_message(status, model, action) -> str:
        """
        Generates a response message based on the status of the response, the model and the action
        performed.

        :param status: Status of the response.
        :type status: :class:`BaCa2FormResponse.Status`
        :param model: Model class which instances the request pertains to.
        :type model: Type[Model]
        :param action: Action performed using the form data.
        :type action: :class:`ModelAction`
        :return: Response message.
        :rtype: str
        """
        model_name = model._meta.verbose_name

        if status == BaCa2FormResponse.Status.SUCCESS:
            return f'successfully performed {action.label} on {model_name}'

        message = f'failed to perform {action.label} on {model_name}'

        if status == BaCa2FormResponse.Status.INVALID:
            message += ' due to invalid form data'
        elif status == BaCa2FormResponse.Status.IMPERMISSIBLE:
            message += ' due to insufficient permissions'
        elif status == BaCa2FormResponse.Status.ERROR:
            message += ' due to an error'

        return message


class BaCa2ModelForm(BaCa2Form):
    """
    Base form for all forms in the BaCa2 system which are used to create, delete or modify
    django model objects.
    """

    #: Model class which instances are affected by the form.
    MODEL: model_cls = None
    #: Action which should be performed using the form data.
    ACTION: ModelAction = None

    def __init__(self, **kwargs):
        super().__init__(initial={'form_name': f'{self.ACTION.label}_form',
                                  'action': self.ACTION.value}, **kwargs)

    @classmethod
    def handle_post_request(cls, request):
        """
        Handles the POST request received by the view this form's data was posted to.

        :param request: Request object.
        :type request: HttpRequest
        """
        if not cls.is_permissible(request):
            return BaCa2ModelFormResponse(
                model=cls.MODEL,
                action=cls.ACTION,
                status=BaCa2FormResponse.Status.IMPERMISSIBLE,
                **cls.handle_impermissible_request(request)
            )

        if cls(data=request.POST).is_valid():
            return BaCa2ModelFormResponse(
                model=cls.MODEL,
                action=cls.ACTION,
                status=BaCa2FormResponse.Status.SUCCESS,
                **cls.handle_valid_request(request)
            )

        return BaCa2ModelFormResponse(
            model=cls.MODEL,
            action=cls.ACTION,
            status=BaCa2FormResponse.Status.INVALID,
            **cls.handle_invalid_request(request)
        )

    @classmethod
    @abstractmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible and the form data is valid.
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @classmethod
    @abstractmethod
    def handle_invalid_request(cls, request) -> Dict[str, str]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible but the form data is invalid.
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @classmethod
    @abstractmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is impermissible.
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

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
