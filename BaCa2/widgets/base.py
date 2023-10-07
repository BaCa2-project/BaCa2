from typing import Dict, Any
from abc import ABC, abstractmethod


class Widget(ABC):
    """
    Base abstract class from which all widgets inherit. Contains any shared logic and methods which
    all widgets have to implement.
    """
    def __init__(self, name: str) -> None:
        """
        Initializes the widget with a name. Name is used to distinguish between widgets of the same
        type within a single HTML template.

        :param name: Name of the widget.
        :type name: str
        """
        self.name = name

    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing all the data needed by the template to render the widget.
        (All boolean values should be converted to JSON strings.)

        :return: A dictionary containing all the data needed to render the widget.
        :rtype: Dict[str, Any]
        """
        pass
