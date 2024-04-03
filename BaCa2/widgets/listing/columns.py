from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict

from django.http import HttpRequest

from widgets.base import Widget
from widgets.forms import FormWidget


class Column(Widget):
    """
    A helper class for the table widget used to define the properties of a table column.

    See also:
        - :class:`widgets.listing.base.TableWidget`
        - :class:`TextColumn`
    """

    #: The template used to render the column header. Must be within the
    #: 'templates/widget_templates/listing' directory.
    template = None

    def __init__(self,
                 *,
                 name: str,
                 col_type: str,
                 request: HttpRequest = None,
                 data_null: bool = False,
                 header: str | None = None,
                 header_icon: str | None = None,
                 searchable: bool = True,
                 search_header: bool = False,
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
        :param header_icon: The icon to be displayed in the column header. If no header text is
            set, the icon will be displayed in place of the header text. If both header text and
            icon are set, the icon will be displayed to the left of the header text.
        :type header_icon: str
        :param searchable: Whether values in the column should be searchable.
        :type searchable: bool
        :param search_header: Whether the column header should be replaced with a column-specific
            search input. Only applicable if searchable is set to True.
        :type search_header: bool
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

        if header is None and header_icon is None:
            header = name

        self.header = header
        self.header_icon = header_icon
        self.col_type = col_type
        self.data_null = data_null
        self.searchable = searchable
        self.search_header = search_header
        self.sortable = sortable
        self.auto_width = auto_width
        self.width = width if width else ''

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'template': f'widget_templates/listing/{self.template}',
            'col_type': self.col_type,
            'header': self.header,
            'header_icon': self.header_icon,
            'data_null': json.dumps(self.data_null),
            'searchable': json.dumps(self.searchable),
            'search_header': self.search_header,
            'sortable': json.dumps(self.sortable),
            'auto_width': json.dumps(self.auto_width),
            'width': self.width
        }

    def data_tables_context(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'col_type': self.col_type,
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

    template = 'text_column.html'

    def __init__(self,
                 *,
                 name: str,
                 header: str | None = None,
                 header_icon: str | None = None,
                 searchable: bool = True,
                 search_header: bool = False,
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
        :param header_icon: The icon to be displayed in the column header. If no header text is
            set, the icon will be displayed in place of the header text. If both header text and
            icon are set, the icon will be displayed to the left of the header text.
        :type header_icon: str
        :param searchable: Whether values in the column should be searchable.
        :type searchable: bool
        :param search_header: Whether the column header should be replaced with a column-specific
            search input. Only applicable if searchable is set to True.
        :type search_header: bool
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
                         header_icon=header_icon,
                         searchable=searchable,
                         search_header=search_header,
                         sortable=sortable,
                         auto_width=auto_width,
                         width=width)


class DatetimeColumn(Column):
    """
        Basic column type for displaying text data.

        See also:
            - :class:`widgets.listing.base.TableWidget`
            - :class:`Column`
        """

    template = 'text_column.html'

    def __init__(self, *,
                 name: str,
                 header: str | None = None,
                 header_icon: str | None = None,
                 formatter: str = 'dd/MM/yyyy H:mm',
                 searchable: bool = True,
                 search_header: bool = False,
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
        :param header_icon: The icon to be displayed in the column header. If no header text is
            set, the icon will be displayed in place of the header text. If both header text and
            icon are set, the icon will be displayed to the left of the header text.
        :type header_icon: str
        :param searchable: Whether values in the column should be searchable.
        :type searchable: bool
        :param search_header: Whether the column header should be replaced with a column-specific
            search input. Only applicable if searchable is set to True.
        :type search_header: bool
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
                         col_type='datetime',
                         data_null=False,
                         header=header,
                         header_icon=header_icon,
                         searchable=searchable,
                         search_header=search_header,
                         sortable=sortable,
                         auto_width=auto_width,
                         width=width)
        self.formatter = formatter

    def data_tables_context(self) -> Dict[str, Any]:
        return super().data_tables_context() | {
            'formatter': self.formatter
        }


class SelectColumn(Column):
    """
    Column used for displaying checkboxes for row selection.

    See also:
        - :class:`widgets.listing.base.TableWidget`
        - :class:`Column`
    """

    template = 'text_column.html'

    def __init__(self) -> None:
        super().__init__(name='select',
                         col_type='select',
                         data_null=True,
                         header='',
                         searchable=False,
                         search_header=False,
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

    template = 'text_column.html'

    def __init__(self) -> None:
        super().__init__(name='delete',
                         col_type='delete',
                         data_null=True,
                         header='',
                         searchable=False,
                         search_header=False,
                         sortable=False,
                         auto_width=False,
                         width='1rem')


class FormSubmitColumn(Column):
    template = 'form_submit_column.html'

    class DisabledAppearance(Enum):
        DISABLED = 'disabled'
        HIDDEN = 'hidden'
        ICON = 'icon'
        TEXT = 'text'

    def __init__(self, *,
                 name: str,
                 form_widget: FormWidget,
                 mappings: Dict[str, str],
                 header: str | None = None,
                 header_icon: str | None = None,
                 btn_text: str = '',
                 btn_icon: str = '',
                 condition_key: str = '',
                 condition_value: str = 'true',
                 disabled_appearance: 'DisabledAppearance' = None,
                 disabled_content: str = '') -> None:
        super().__init__(name=name,
                         col_type='form-submit',
                         data_null=True,
                         header=header,
                         header_icon=header_icon,
                         searchable=False,
                         search_header=False,
                         sortable=False,
                         auto_width=False,
                         width='1rem')

        if not btn_text and not btn_icon:
            raise ValueError('Either btn_text or btn_icon must be set.')

        for key in mappings.keys():
            if key not in form_widget.form.fields.keys():
                raise ValueError(f'Key "{key}" not found in form fields.')

        self.form_widget = form_widget
        self.mappings = mappings
        self.btn_text = btn_text
        self.btn_icon = btn_icon
        self.condition_key = condition_key
        self.condition_value = condition_value

        if not disabled_appearance:
            disabled_appearance = self.DisabledAppearance.DISABLED

        self.disabled_appearance = disabled_appearance
        self.disabled_content = disabled_content

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'form_widget': self.form_widget.get_context(),
        }

    def data_tables_context(self) -> Dict[str, Any]:
        return super().data_tables_context() | {
            'form_id': self.form_widget.name,
            'mappings': json.dumps(self.mappings),
            'btn_text': self.btn_text,
            'btn_icon': self.btn_icon,
            'conditional': json.dumps(bool(self.condition_key)),
            'condition_key': self.condition_key,
            'condition_value': self.condition_value,
            'disabled_appearance': self.disabled_appearance.value,
            'disabled_content': self.disabled_content
        }
