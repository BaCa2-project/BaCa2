from abc import ABC
from typing import Any, Callable, Dict, Iterable

from django.http import HttpRequest


class Widget(ABC):  # noqa: B024
    """
    Base abstract class from which all widgets inherit. Contains any shared logic and methods which
    all widgets have to implement.
    """

    class ParameterError(Exception):
        """
        Exception raised when a widget receives an invalid parameter or combination of parameters.
        """
        pass

    class NotBuiltError(Exception):
        """
        Exception raised when an operation is attempted on a widget that has not been built yet
        which requires the widget to be built.
        """

    @staticmethod
    def require_built(func) -> Callable:
        """
        Decorator that raises an exception if the decorated method is called on a widget that has
        not been built yet.

        :param func: Method to decorate.
        :type func: Callable
        :return: Decorated method.
        :rtype: Callable
        """
        def wrapper(self, *args, **kwargs):
            if not getattr(self, 'built', False):
                raise Widget.NotBuiltError('Widget has not been built yet.')
            return func(self, *args, **kwargs)
        return wrapper

    def __init__(self, *,
                 name: str,
                 request: HttpRequest = None,
                 widget_class: str | Iterable[str] = '') -> None:
        """
        :param name: Name of the widget. Used to identify the widget in the template.
        :type name: str
        :param request: HTTP request object received by the view this widget is rendered in.
        :type request: HttpRequest
        :param widget_class: HTML class(es) applied to the widget when rendered.
        :type widget_class: str | Iterable[str]
        """
        self._built = False
        self.name = name
        self.request = request
        self._widget_class = set()
        self.widget_class = widget_class

    def build(self) -> None:
        """
        Builds the widget. This method is called once all the parameters have been set to perform
        all the necessary state-altering operations before the widget is rendered.
        """
        self._built = True

    @property
    def built(self) -> bool:
        """
        :return: Whether the widget has been built yet.
        :rtype: bool
        """
        return self._built

    @property
    def widget_class(self) -> str:
        """
        :return: HTML class of the rendered widget.
        :rtype: str
        """
        return ' '.join(self._widget_class)

    @widget_class.setter
    def widget_class(self, value: str | Iterable[str]) -> None:
        """
        :param value: HTML class(es) to set.
        :type value: str | Iterable[str]
        """
        if isinstance(value, list):
            value = ' '.join(value)

        self._widget_class = set(value.split(' '))

    def add_class(self, widget_class: str) -> None:
        """
        :param widget_class: HTML class to add.
        :type widget_class: str
        """
        for cls in widget_class.split(' '):
            self._widget_class.add(cls)

    def remove_class(self, widget_class: str) -> None:
        """
        :param widget_class: HTML class to remove.
        :type widget_class: str
        """
        for cls in widget_class.split(' '):
            self._widget_class.discard(cls)

    def get_context(self) -> Dict[str, Any]:
        """
        :return: A dictionary containing all the data needed to render the widget.
        :rtype: Dict[str, Any]
        """
        return {'name': self.name, 'widget_class': self.widget_class}
