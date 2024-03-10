from pathlib import Path

from django.utils.translation import gettext_lazy as _

from widgets.base import Widget


class CodeBlock(Widget):
    class UnknownLanguageError(Exception):
        pass

    def __init__(self,
                 name: str,
                 code: str | Path,
                 language: str = None,
                 title: str = None,
                 show_line_numbers: bool = True,
                 wrap_lines: bool = True,
                 display_wrapper: bool = True):
        super().__init__(name=name)

        if not title:
            title = _('Code block')
        self.title = title

        if isinstance(code, Path):
            with open(code, 'r') as f:
                self.code = f.read()
            self.language = language or code.suffix[1:]
            if language:
                self.language = language
        else:
            self.code = code
            self.language = language

        if not self.language:
            raise self.UnknownLanguageError('Language must be provided if code is a string.')

        self.show_line_numbers = show_line_numbers
        self.display_wrapper = display_wrapper

        if wrap_lines:
            self.add_class('wrap-lines')

    def get_context(self) -> dict:
        return super().get_context() | {
            'name': self.name,
            'title': self.title,
            'language': self.language,
            'code': self.code,
            'show_line_numbers': self.show_line_numbers,
            'display_wrapper': self.display_wrapper,
        }
