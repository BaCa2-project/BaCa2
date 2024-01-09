from __future__ import annotations

from typing import Dict, Any
import json

from django.http import HttpRequest

from widgets.base import Widget


class Column(Widget):
    def __init__(self,
                 name: str,
                 col_type: str,
                 request: HttpRequest = None,
                 data_null: bool = False,
                 header: str | None = None,
                 searchable: bool = True,
                 sortable: bool = False,
                 auto_width: bool = True,
                 width: str | None = None) -> None:
        if auto_width and width:
            raise self.WidgetParameterError('Cannot set column width when auto width is enabled.')
        if not auto_width and not width:
            raise self.WidgetParameterError('Must set column width when auto width is disabled.')

        super().__init__(name=name, request=request)
        if header is None:
            header = name
        self.header = header
        self.col_type = col_type
        self.data_null = data_null
        self.searchable = searchable
        self.sortable = sortable
        self.auto_width = auto_width
        self.width = width if width else ''

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'col_type': self.col_type,
            'header': self.header,
            'data_null': json.dumps(self.data_null),
            'searchable': json.dumps(self.searchable),
            'sortable': json.dumps(self.sortable),
            'auto_width': json.dumps(self.auto_width),
            'width': self.width
        }


class TextColumn(Column):
    def __init__(self,
                 name: str,
                 header: str | None = None,
                 searchable: bool = True,
                 sortable: bool = True,
                 auto_width: bool = True,
                 width: str | None = None) -> None:
        super().__init__(name=name,
                         col_type='text',
                         data_null=False,
                         header=header,
                         searchable=searchable,
                         sortable=sortable,
                         auto_width=auto_width,
                         width=width)


class SelectColumn(Column):
    def __init__(self) -> None:
        super().__init__(name='select',
                         col_type='select',
                         data_null=True,
                         header='',
                         searchable=False,
                         sortable=False,
                         auto_width=False,
                         width='1rem')


class DeleteColumn(Column):
    def __init__(self) -> None:
        super().__init__(name='delete',
                         col_type='delete',
                         data_null=True,
                         header='',
                         searchable=False,
                         sortable=False,
                         auto_width=False,
                         width='1rem')
