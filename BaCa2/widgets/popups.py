from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from widgets.base import Widget


class PopupWidget(Widget):
    """
    Base class for all popup widgets. Contains context fields common to all popups.

    See Also:
        - :class:`widgets.base.Widget`
    """
    def __init__(self,
                 name: str,
                 title: str,
                 message: str,
                 popup_class: str = "") -> None:
        """
        :param name: Name of the widget.
        :type name: str
        :param title: Title of the popup.
        :type title: str
        :param message: Message of the popup.
        :type message: str
        :param popup_class: CSS class applied to the popup.
        :type popup_class: str
        """
        super().__init__(name=name, widget_class=popup_class)
        self.title = title
        self.message = message

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'message': self.message,
        }


class FormConfirmationPopup(PopupWidget):
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
                 confirm_button_text: str = _('Confirm'),
                 cancel_button_text: str = _('Cancel'),
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
        if input_summary and not input_summary_fields:
            raise Widget.WidgetParameterError(
                "Cannot use input summary without specifying input summary fields."
            )

        super().__init__(name=name,
                         title=title,
                         message=message,
                         popup_class="form-confirmation-popup")
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
