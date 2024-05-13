from abc import ABC
from typing import Any, Dict

from django.http import HttpRequest


class Widget(ABC):  # noqa: B024
    """
    Base abstract class from which all widgets inherit. Contains any shared logic and methods which
    all widgets have to implement.
    """

    class WidgetParameterError(Exception):
        """
        Exception raised when a widget receives an invalid parameter or combination of parameters.
        """
        pass

    def __init__(self, name: str, request: HttpRequest = None, widget_class: str = '') -> None:
        """
        Initializes the widget with a name. Name is used to distinguish between widgets of the same
        type within a single HTML template.

        :param name: Name of the widget.
        :type name: str
        :param request: HTTP request object received by the view this widget is rendered in.
        :type request: HttpRequest
        :param widget_class: CSS class applied to the widget.
        :type widget_class: str
        """
        self.name = name
        self.request = request
        self.widget_class = set(widget_class.split(' '))

    def add_class(self, widget_class: str) -> None:
        """
        Adds a CSS class to the widget.

        :param widget_class: CSS class to add.
        :type widget_class: str
        """
        for cls in widget_class.split(' '):
            self.widget_class.add(cls)

    def remove_class(self, widget_class: str) -> None:
        """
        Removes a CSS class from the widget.

        :param widget_class: CSS class to remove.
        :type widget_class: str
        """
        for cls in widget_class.split(' '):
            self.widget_class.discard(cls)

    def get_context(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing all the data needed by the template to render the widget.
        (All boolean values should be converted to JSON strings.)

        :return: A dictionary containing all the data needed to render the widget.
        :rtype: Dict[str, Any]
        """
        return {'name': self.name, 'widget_class': ' '.join(self.widget_class)}
