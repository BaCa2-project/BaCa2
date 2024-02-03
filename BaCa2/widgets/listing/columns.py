from __future__ import annotations

import json
from typing import Any, Dict

from django.http import HttpRequest

from widgets.base import Widget


class Column(Widget):
    """
    A helper class for the table widget used to define the properties of a table column.

    See also:
        - :class:`widgets.listing.base.TableWidget`
        - :class:`TextColumn`
    """
    def __init__(self,
                 *,
                 name: str,
                 col_type: str,
                 request: HttpRequest = None,
                 data_null: bool = False,
                 header: str | None = None,
                 searchable: bool = True,
                 sortable: bool = False,
                 auto_width: bool = True,
                 width: str | None = None) -> None:
        """
        :param name: The name of the column. This should be the same as the key under which
            the column's data can be found in the data dictionary retrieved by the table widget.
        :type name: str
        :param col_type: The type of the column. This is used to determine how the data in the
            column should be displayed.
        :type col_type: str
        :param request: The HTTP request object received by the view in which the table widget
            is rendered.
        :type request: HttpRequest
        :param data_null: Whether the column displays data retrieved from the table's data source.
            should be set to True for all special columns not based on retrieved data, such as the
            select and delete columns.
        :type data_null: bool
        :param header: The text to be displayed in the column header. If not set, the column name
            will be used instead.
        :type header: str
        :param searchable: Whether values in the column should be searchable.
        :type searchable: bool
        :param sortable: Whether the column should be sortable.
        :type sortable: bool
        :param auto_width: Whether the column width should be determined automatically. If set to
            False, the width parameter must be set.
        :type auto_width: bool
        :param width: The width of the column. This parameter should only be set if auto_width is
            set to False.
        :type width: str
        """
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
    """
    Basic column type for displaying text data.

    See also:
        - :class:`widgets.listing.base.TableWidget`
        - :class:`Column`
    """
    def __init__(self,
                 *,
                 name: str,
                 header: str | None = None,
                 searchable: bool = True,
                 sortable: bool = True,
                 auto_width: bool = True,
                 width: str | None = None) -> None:
        """
        :param name: The name of the column. This should be the same as the key under which
            the column's data can be found in the data dictionary retrieved by the table widget.
        :type name: str
        :param header: The text to be displayed in the column header. If not set, the column name
            will be used instead.
        :type header: str
        :param searchable: Whether values in the column should be searchable.
        :type searchable: bool
        :param sortable: Whether the column should be sortable.
        :type sortable: bool
        :param auto_width: Whether the column width should be determined automatically. If set to
            False, the width parameter must be set.
        :type auto_width: bool
        :param width: The width of the column. This parameter should only be set if auto_width is
            set to False.
        :type width: str
        """
        super().__init__(name=name,
                         col_type='text',
                         data_null=False,
                         header=header,
                         searchable=searchable,
                         sortable=sortable,
                         auto_width=auto_width,
                         width=width)


class SelectColumn(Column):
    """
    Column used for displaying checkboxes for row selection.

    See also:
        - :class:`widgets.listing.base.TableWidget`
        - :class:`Column`
    """
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
    """
    Column used for displaying delete buttons for record deletion.

    See also:
        - :class:`widgets.listing.base.TableWidget`
        - :class:`Column`
    """
    def __init__(self) -> None:
        super().__init__(name='delete',
                         col_type='delete',
                         data_null=True,
                         header='',
                         searchable=False,
                         sortable=False,
                         auto_width=False,
                         width='1rem')
