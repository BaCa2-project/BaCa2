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

    def __init__(self, name: str, file_path: Path) -> None:
        """
        :param name: Name of the widget.
        :type name: str
        :param file_path: Path to the file to be displayed. File must be in HTML, Markdown, or plain
            text format.
        :type file_path: Path
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

    def get_context(self) -> dict:
        return super().get_context() | {'content': self.content}
