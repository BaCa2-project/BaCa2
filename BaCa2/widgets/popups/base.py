from typing import Dict, Any

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
