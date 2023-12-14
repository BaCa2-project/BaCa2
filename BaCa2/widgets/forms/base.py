from __future__ import annotations

from typing import (Dict, List, Any)
from enum import Enum
from abc import ABC, abstractmethod

from django import forms
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from util.models import model_cls
from util.models_registry import ModelsRegistry
from BaCa2.choices import ModelAction
from main.models import Course


class FormWidget(Widget):
    """
    Base widget for forms. Responsible for generating the context dictionary necessary for rendering
    the form. The default template used for rendering the form is:
    `BaCa2/templates/widget_templates/forms/default.html`.
    FormWidget __init__ method arguments control the rendered form's behaviour and appearance.
    """

    class FormWidgetException(Exception):
        """
        Exception raised when an error related to incongruence in the parameters of the FormWidget
        class occurs.
        """
        pass

    def __init__(self,
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
                 confirmation_popup: FormConfirmationPopup = None) -> None:
        if not name:
            form_name = getattr(form, 'form_name', False)
            if form_name:
                name = f'{form_name}_widget'
            else:
                raise FormWidget.FormWidgetException(
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
        self.confirmation_popup = confirmation_popup

        if confirmation_popup:
            self.confirmation_popup.name = f'{self.name}_confirmation_popup'

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
            'confirmation_popup': self.confirmation_popup
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


class FormConfirmationPopup(Widget):
    def __init__(self,
                 title: str,
                 description: str,
                 confirm_button_text: str = _('Confirm'),
                 cancel_button_text: str = _('Cancel'),
                 input_summary: bool = False,
                 input_summary_fields: List[str] = None) -> None:
        if input_summary and not input_summary_fields:
            raise FormWidget.FormWidgetException(
                "Cannot use input summary without specifying input summary fields."
            )

        super().__init__('')
        self.title = title
        self.description = description
        self.confirm_button_text = confirm_button_text
        self.cancel_button_text = cancel_button_text
        self.input_summary = input_summary
        self.input_summary_fields = input_summary_fields

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'description': self.description,
            'input_summary': self.input_summary,
            'input_summary_fields': self.input_summary_fields,
            'confirm_button_text': self.confirm_button_text,
            'cancel_button_text': self.cancel_button_text
        }


class BaCa2Form(forms.Form):
    """
    Base form for all forms in the BaCa2 system. Contains shared, hidden fields
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


class BaCa2ModelForm(BaCa2Form):
    """
    Base form for all forms in the BaCa2 system which are used to create, delete or modify
    django model objects.
    """

    #: Model class which instances are affected by the form.
    MODEL: model_cls = None
    #: Action which should be performed using the form data.
    ACTION: ModelAction = None

    class Status(Enum):
        """
        Enum used to indicate the possible outcomes of a post request sent via a model form.
        A JSON response returned by the handle_post_request method of a model will always contain
        a status field with one of the values from this enum.
        """
        #: Indicates that the request was successful.
        SUCCESS = 'success'
        #: Indicates that the request was unsuccessful due to invalid form data.
        INVALID = 'invalid'
        #: Indicates that the request was unsuccessful due to the user not having the permission to
        # perform the action specified by the form.
        IMPERMISSIBLE = 'impermissible'
        #: Indicates that the request was unsuccessful due to an error not related to form
        # validation or the user's permissions.
        ERROR = 'error'

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
            return JsonResponse(
                {'status': cls.Status.IMPERMISSIBLE.value} |
                cls.handle_impermissible_request(request)
            )

        if cls(data=request.POST).is_valid():
            return JsonResponse(
                {'status': cls.Status.SUCCESS.value} |
                cls.handle_valid_request(request)
            )

        return JsonResponse(
            {'status': cls.Status.INVALID.value} |
            cls.handle_invalid_request(request)
        )

    @classmethod
    @abstractmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible and the form data is valid.
        """
        pass

    @classmethod
    @abstractmethod
    def handle_invalid_request(cls, request) -> Dict[str, str]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is permissible but the form data is invalid.
        """
        pass

    @classmethod
    @abstractmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        """
        Handles the POST request received by the view this form's data was posted to if the request
        is impermissible.
        """
        pass

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
