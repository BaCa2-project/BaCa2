from typing import Dict, Any
from enum import Enum

from widgets.base import Widget


class PopupWidget(Widget):
    """
    Base class for all popup widgets. Contains context fields common to all popups.

    See Also:
        - :class:`widgets.base.Widget`
    """

    class PopupSize(Enum):
        """
        Enum representing the possible sizes of a popup. Values are CSS Bootstrap classes.
        """
        SMALL = "modal-sm"
        MEDIUM = ""
        LARGE = "modal-lg"
        EXTRA_LARGE = "modal-xl"

    def __init__(self,
                 *,
                 name: str,
                 title: str,
                 message: str,
                 widget_class: str = "",
                 size: PopupSize = PopupSize.MEDIUM) -> None:
        """
        :param name: Name of the widget.
        :type name: str
        :param title: Title of the popup.
        :type title: str
        :param message: Message of the popup.
        :type message: str
        :param widget_class: CSS class applied to the popup.
        :type widget_class: str
        :param size: Size of the popup.
        :type size: :class:`PopupWidget.PopupSize`
        """
        super().__init__(name=name, widget_class=widget_class)
        self.title = title
        self.message = message
        self.add_class(size.value)

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'message': self.message,
        }
