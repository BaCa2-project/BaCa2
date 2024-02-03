from typing import Any, Dict, List

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from widgets.popups.base import PopupWidget


class SubmitConfirmationPopup(PopupWidget):
    """
    A popup widget used to confirm a form submission. Can optionally display a summary of the form
    data.

    See Also:
        - :class:`widgets.forms.FormWidget`
        - :class:`widgets.popups.PopupWidget`
    """

    def __init__(self,
                 title: str,
                 message: str,
                 name: str = '',
                 request: HttpRequest = None,
                 confirm_button_text: str = None,
                 cancel_button_text: str = None,
                 input_summary: bool = False,
                 input_summary_fields: List[str] = None) -> None:
        """
        :param title: Title of the popup.
        :type title: str
        :param message: Message of the popup.
        :type message: str
        :param name: Name of the widget. Will normally be automatically provided by a parent form
            widget.
        :type name: str
        :param request: HTTP request object received by the view this popup is rendered in. Provided
            by the parent form widget.
        :type request: HttpRequest
        :param confirm_button_text: Text displayed on the submission confirmation button.
        :type confirm_button_text: str
        :param cancel_button_text: Text displayed on the submission cancellation button.
        :type cancel_button_text: str
        :param input_summary: Whether to display a summary of the form data.
        :type input_summary: bool
        :param input_summary_fields: List of field names to display in the input summary.
        :type input_summary_fields: List[str]
        :raises Widget.WidgetParameterError: If input summary is enabled without specifying input
            summary fields.
        """
        if confirm_button_text is None:
            confirm_button_text = _('Confirm')
        if cancel_button_text is None:
            cancel_button_text = _('Cancel')

        if input_summary and not input_summary_fields:
            raise Widget.WidgetParameterError(
                'Cannot use input summary without specifying input summary fields.'
            )

        super().__init__(name=name,
                         request=request,
                         title=title,
                         message=message,
                         widget_class='form-confirmation-popup',
                         size=PopupWidget.PopupSize.MEDIUM)
        self.confirm_button_text = confirm_button_text
        self.cancel_button_text = cancel_button_text
        self.input_summary = input_summary
        self.input_summary_fields = input_summary_fields

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'input_summary': self.input_summary,
            'input_summary_fields': self.input_summary_fields,
            'confirm_button_text': self.confirm_button_text,
            'cancel_button_text': self.cancel_button_text
        }


class SubmitSuccessPopup(PopupWidget):
    """
    A popup widget used to display a success message after a form submission. Can display either a
    predefined message or a message received in the JSON response from the server.

    See Also:
        - :class:`widgets.forms.FormWidget`
        - :class:`widgets.popups.PopupWidget`
    """

    def __init__(self,
                 title: str = None,
                 message: str = '',
                 name: str = '',
                 request: HttpRequest = None,
                 confirm_button_text: str = None) -> None:
        """
        :param title: Title of the popup. Defaults to "Success".
        :type title: str
        :param message: Message of the popup. If not specified, the message received in the JSON
            response from the server will be used instead.
        :type message: str
        :param name: Name of the widget. Will normally be automatically provided by a parent form
            widget.
        :type name: str
        :param request: HTTP request object received by the view this popup is rendered in. Provided
            by the parent form widget.
        :type request: HttpRequest
        :param confirm_button_text: Text displayed on the confirmation button. Defaults to "OK".
        :type confirm_button_text: str
        """
        if title is None:
            title = _('Success')
        if confirm_button_text is None:
            confirm_button_text = _('OK')

        super().__init__(name=name,
                         request=request,
                         title=title,
                         message=message,
                         widget_class='form-success-popup',
                         size=PopupWidget.PopupSize.SMALL)
        self.confirm_button_text = confirm_button_text

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'confirm_button_text': self.confirm_button_text
        }


class SubmitFailurePopup(PopupWidget):
    """
    A popup widget used to display a failure message after a form submission. Can display either a
    predefined message or a message received in the JSON response from the server.

    See Also:
        - :class:`widgets.forms.FormWidget`
        - :class:`widgets.popups.PopupWidget`
    """

    def __init__(self,
                 title: str = None,
                 message: str = '',
                 name: str = '',
                 request: HttpRequest = None,
                 confirm_button_text: str = None) -> None:
        """
        :param title: Title of the popup. Defaults to "Failure".
        :type title: str
        :param message: Message of the popup. If not specified, the message received in the JSON
            response from the server will be used instead.
        :type message: str
        :param name: Name of the widget. Will normally be automatically provided by a parent form
            widget.
        :type name: str
        :param request: HTTP request object received by the view this popup is rendered in. Provided
            by the parent form widget.
        :type request: HttpRequest
        :param confirm_button_text: Text displayed on the confirmation button. Defaults to "OK".
        :type confirm_button_text: str
        """
        if title is None:
            title = _('Failure')
        if confirm_button_text is None:
            confirm_button_text = _('OK')

        super().__init__(name=name,
                         request=request,
                         title=title,
                         message=message,
                         widget_class='form-failure-popup',
                         size=PopupWidget.PopupSize.SMALL)
        self.confirm_button_text = confirm_button_text

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'confirm_button_text': self.confirm_button_text
        }
