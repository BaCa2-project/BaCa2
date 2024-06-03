import logging
from pathlib import Path
from typing import Self

from django.utils.translation import gettext_lazy as _

from widgets.base import Widget

logger = logging.getLogger(__name__)


class CodeBlock(Widget):
    """
    Widget used to display code blocks with syntax highlighting.
    """

    class UnknownLanguageError(Exception):
        """
        Exception raised when the widget was not able to determine the language of the code.
        """
        pass

    def __init__(self, *,
                 name: str,
                 code: str | Path,
                 language: str = '',
                 title: str = '',
                 line_numbers: bool = True,
                 wrap_lines: bool = True,
                 display_wrapper: bool = True):
        """
        :param name: Name of the code block. Unique within view context scope.
        :type name: str
        :param code: Code to display in the code block. Can be a string or a path to a file. If
            provided as a string, the language must be specified.
        :type code: str | Path
        :param language: Language of the code. Used for syntax highlighting. Must be specified if
            the code is provided as a string.
        :type language: str
        :param title: Title of the code block. Displayed above the code if display_wrapper is set to
            True.
        :type title: str
        :param line_numbers: Whether to initialize the code block with line numbers. Line numbers
            can be toggled on and off by the user using a toolbar button.
        :type line_numbers: bool
        :param wrap_lines: Whether to initialize the code block with line wrapping enabled. Line
            wrapping can be toggled on and off by the user using a toolbar button.
        :type wrap_lines: bool
        :param display_wrapper: Whether to display the code block inside a wrapper element with a
            title.
        :type display_wrapper: bool
        """
        super().__init__(name=name, widget_class='code-block m-0')
        self.title = title
        self.language = language
        self.code = code
        self.line_numbers = line_numbers
        self.display_wrapper = display_wrapper
        self.wrap_lines = wrap_lines

    def build(self) -> Self:
        if not self.language:
            raise self.UnknownLanguageError('Language must be provided if code is a string.')

        if self.code is None:
            self._code = _('ERROR: Failed to read file.\n '
                           'Make sure you have sent valid file as solution.')
            self.language = 'log'

        if self.wrap_lines:
            self.add_class('wrap-lines')
        if self.line_numbers:
            self.add_class('line-numbers')

        self.title = self.title or _('Code block')

        return super().build()

    @property
    def code(self) -> str:
        """
        :return: Code to display in the code block.
        :rtype: str
        """
        return self._code

    @code.setter
    def code(self, value: str | Path) -> None:
        """
        :param value: Code to display in the code block. Can be a string or a path to a file. If
            provided as a string, the language must be specified.
        :type value: str | Path
        """
        if isinstance(value, Path):
            self._read_code_from_file(value)
            return
        if not self.language:
            logger.warning('Language must be provided if code is a string.')
        self._code = value

    def _read_code_from_file(self, code: Path) -> None:
        """
        Attempts to read the code from a file. If successful, sets the code and language attributes
        of the widget. If not, sets the code attribute to None (replaced with an error message at
        build time).

        :param code: Path to the file containing the code.
        :type code: Path
        """
        try:
            with open(code, 'r', encoding='utf-8') as f:
                self.code = f.read()
            self.language = self.language or code.suffix[1:]
        except Exception as e:
            logger.warning(f'Failed to read file {code}: {e.__class__.__name__}: {e}')
            self.code = None

    def get_context(self) -> dict:
        return super().get_context() | {
            'name': self.name,
            'title': self.title,
            'language': self.language,
            'code': self.code,
            'display_wrapper': self.display_wrapper,
        }
