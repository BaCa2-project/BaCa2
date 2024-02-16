from enum import Enum
from pathlib import Path

from markdown import markdown
from mdx_math import MathExtension
from widgets.base import Widget


class MarkupDisplayer(Widget):
    """
    Widget used to display the contents of files in HTML, Markdown, or plain text format. Supports
    LaTeX math in Markdown files.
    """

    class AcceptedFormats(Enum):
        """
        Enum containing all the file formats supported by the widget.
        """
        HTML = '.html'
        MARKDOWN = '.md'
        TEXT = '.txt'

    def __init__(self,
                 name: str,
                 file_path: Path,
                 line_height: float = 1.2,
                 limit_display_height: bool = True,
                 display_height: int = 50) -> None:
        """
        :param name: Name of the widget.
        :type name: str
        :param file_path: Path to the file to be displayed. File must be in HTML, Markdown, or plain
            text format.
        :type file_path: Path
        :param line_height: Line height of the displayed text in `rem` units. Default is 1.2.
        :type line_height: float
        :param limit_display_height: Whether to limit the height of the displayed text. If set to
            `True`, the height of the displayed text will be limited to `display_height` lines of
            text.
        :type limit_display_height: bool
        :param display_height: Height of the displayed text in number of standard height lines.
            Only used if `limit_display_height` is set to `True`. Default is 50.
        :type display_height: int
        """
        super().__init__(name=name)

        suffix = file_path.suffix

        if suffix not in {extension.value for extension in self.AcceptedFormats}:
            raise self.WidgetParameterError('File format not supported.')

        with file_path.open('r', encoding='utf-8') as file:
            self.content = file.read()

        if suffix == self.AcceptedFormats.MARKDOWN.value:
            self.content = markdown(self.content, extensions=[MathExtension()])
        elif suffix == self.AcceptedFormats.TEXT.value:
            self.content = self.content.replace('\n', '<br>')

        self.line_height = f'{round(line_height, 2)}rem'
        self.limit_display_height = limit_display_height
        self.display_height = f'{round(display_height * line_height, 2)}rem'

    def get_context(self) -> dict:
        return super().get_context() | {
            'content': self.content,
            'line_height': self.line_height,
            'limit_display_height': self.limit_display_height,
            'display_height': self.display_height
        }
