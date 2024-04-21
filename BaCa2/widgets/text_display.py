from enum import Enum
from pathlib import Path

from django.utils.translation import gettext_lazy as _

from markdown import markdown
from mdx_math import MathExtension
from widgets.base import Widget


class TextDisplayer(Widget):
    """
    Wrapper widget which selects the appropriate displayer widget based on the format of the file
    provided. If no file is provided, a special case displayer widget is used to display a message
    in place of the file.
    """

    class EmptyDisplayer(Widget):
        """
        Special case displayer widget used when no file to display is provided. Will be rendered
        as a specified message (defaulting to "No file to display").
        """
        def __init__(self, name: str, message: str = None) -> None:
            """
            :param name: Name of the widget.
            :type name: str
            :param message: Message to be displayed in place of the file.
            :type message: str
            """
            if message is None:
                message = _('No file to display')
            super().__init__(name=name)
            self.message = message

        def get_context(self) -> dict:
            return super().get_context() | {'message': self.message}

    def __init__(self,
                 name: str,
                 file_path: Path,
                 download_name: str = '',
                 no_file_message: str = None,
                 **kwargs) -> None:
        """
        :param name: Name of the widget.
        :type name: str
        :param file_path: Path to the file to be displayed. File should PDF, HTML, Markdown, or
            plain text. If no file is provided, a special case displayer widget will be used to
            display a message in place of the file.
        :type file_path: Path
        :param download_name: Name of the file to be downloaded if text displayer offers a PDF
            download option. Default is the name of the file.
        :type download_name: str
        :param no_file_message: Message to be displayed in place of the file if no file is provided.
            Default is "No file to display".
        :type no_file_message: str
        :param kwargs: Additional keyword arguments to be passed to the specific displayer widget
            selected based on the format of the file provided.
        :type kwargs: dict
        """
        if no_file_message is None:
            no_file_message = _('No file to display')
        super().__init__(name=name)

        if not file_path:
            self.displayer_type = 'none'
            self.displayer = self.EmptyDisplayer(name=name, message=no_file_message)
        elif file_path.suffix == '.pdf':
            self.displayer_type = 'pdf'
            self.displayer = PDFDisplayer(name=name,
                                          file_path=file_path,
                                          download_name=download_name)
        else:
            self.displayer_type = 'markup'
            self.displayer = MarkupDisplayer(name=name,
                                             file_path=file_path,
                                             pdf_download_name=download_name,
                                             **kwargs)

    def get_context(self) -> dict:
        return super().get_context() | {
            'displayer_type': self.displayer_type,
            'displayer': self.displayer.get_context()
        }


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
                 display_height: int = 40,
                 pdf_download: Path = None,
                 pdf_download_name: str = '') -> None:
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
        :param pdf_download: Path to the PDF file to be downloaded. If provided, a download button
            will be displayed above the text.
        :type pdf_download: Path
        :param pdf_download_name: Name of the PDF file to be downloaded. Default is the name of the
            file.
        :type pdf_download_name: str
        """
        super().__init__(name=name)

        suffix = file_path.suffix

        if suffix not in {extension.value for extension in self.AcceptedFormats}:
            raise self.WidgetParameterError(f'File format {suffix} not supported.')

        with file_path.open('r', encoding='utf-8') as file:
            self.content = file.read()

        if suffix == self.AcceptedFormats.MARKDOWN.value:
            self.content = markdown(self.content, extensions=[MathExtension()])
        elif suffix == self.AcceptedFormats.TEXT.value:
            self.content = self.content.replace('\n', '<br>')\

        if pdf_download:
            if pdf_download.suffix != '.pdf':
                raise self.WidgetParameterError(f'File format {suffix} not supported.')
            self.pdf_download = str(pdf_download.name).replace('\\', '/')
        else:
            self.pdf_download = False

        if not pdf_download_name:
            pdf_download_name = pdf_download.name
        self.pdf_download_name = pdf_download_name

        self.line_height = f'{round(line_height, 2)}rem'
        self.limit_display_height = limit_display_height
        self.display_height = f'{round(display_height * line_height, 2)}rem'

    def get_context(self) -> dict:
        return super().get_context() | {
            'content': self.content,
            'line_height': self.line_height,
            'limit_display_height': self.limit_display_height,
            'display_height': self.display_height,
            'pdf_download': self.pdf_download,
            'pdf_download_name': self.pdf_download_name
        }


class PDFDisplayer(Widget):
    """
    Widget used to display PDF files.
    """

    def __init__(self, name: str, file_path: Path, download_name: str = '') -> None:
        """
        :param name: Name of the widget.
        :type name: str
        :param file_path: Path to the PDF file to be displayed.
        :type file_path: Path
        :param download_name: Name of the file to be downloaded. Default is the name of the file.
        :type download_name: str
        """
        super().__init__(name=name)

        suffix = file_path.suffix

        if suffix != '.pdf':
            raise self.WidgetParameterError(f'File format {suffix} not supported.')

        self.file_path = str(file_path.name).replace('\\', '/')

        if not download_name:
            download_name = file_path.name
        self.download_name = download_name

    def get_context(self) -> dict:
        return super().get_context() | {
            'file_path': self.file_path,
            'download_name': self.download_name
        }
