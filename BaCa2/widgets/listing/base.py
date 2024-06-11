from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Self

from django.http import HttpRequest
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from widgets.forms import BaCa2ModelForm, FormWidget
from widgets.listing.columns import Column, DeleteColumn, SelectColumn
from widgets.popups.forms import SubmitConfirmationPopup

logger = logging.getLogger(__name__)


class TableWidget(Widget):
    """
    Widget used to display a table of data. Constructor arguments define the table's properties
    such as title, columns, data source, search options, etc.

    The table widget is rendered with the help of the DataTables jQuery plugin using the
    `templates/widget_templates/table.html` template.

    All table widgets used to display database records should fetch their data with an AJAX get
    request to the appropriate model view. As such their data source should be set to the url of
    the model view from which they receive their data (generated using the `get_url` method of the
    model view class). The data source url should return a JSON object containing a 'data' key with
    a list of dictionaries representing table rows. The keys of the dictionaries should
    correspond to the names of the table columns.

    If the table widget is used to display static data, the data source should be provided as a
    list of dictionaries representing table rows. The keys of the dictionaries should correspond to
    the names of the table columns. All records in the table should have the same keys as well as
    an 'id' key. If the provided dictionaries do not contain an 'id' key, the table widget will
    automatically generate unique ids for the records.
    """

    LOCALISATION = {
        'pl': '//cdn.datatables.net/plug-ins/2.0.3/i18n/pl.json',
    }

    def __init__(self, *,
                 name: str,
                 data_source: str | List[Dict[str, Any]],
                 cols: List[Column],
                 request: HttpRequest | None = None,
                 title: str = '',
                 display_title: bool = True,
                 allow_global_search: bool = True,
                 allow_select: bool = False,
                 deselect_on_filter: bool = True,
                 allow_delete: bool = False,
                 delete_form: BaCa2ModelForm = None,
                 data_post_url: str = '',
                 paging: TableWidgetPaging = None,
                 table_height: int | None = None,
                 resizable_height: bool = False,
                 link_format_string: str | bool = False,
                 refresh_button: bool = False,
                 refresh: bool = False,
                 refresh_interval: int = 30,
                 default_sorting: bool = True,
                 default_order_col: str | None = None,
                 default_order_asc: bool = True,
                 stripe_rows: bool = True,
                 highlight_rows_on_hover: bool = False,
                 hide_col_headers: bool = False,
                 row_styling_rules: List[RowStylingRule] = None,
                 language: str = 'pl', ) -> None:
        """
        :param name: The name of the table widget. Names are used as ids for the HTML <table>
            elements of the rendered table widgets.
        :type name: str
        :param data_source: Data source used to populate the table. If the table is used to display
            static data, the data source should be provided as a list of dictionaries representing
            table rows. The keys of the dictionaries should correspond to the names of the table
            columns. If the table is used to display database records, the data source should be
            set to the url of the view from which the table receives its data. The data source
            should return a JSON object containing a 'data' key with a list of dictionaries
            representing table rows. The keys of the dictionaries should correspond to the names of
            the table columns.
        :type data_source: str | List[Dict[str, Any]]
        :param cols: List of columns to be displayed in the table. Each column object defines the
            column's properties such as name, header, searchability, etc.
        :type cols: List[:class:`Column`]
        :param request: The HTTP request object received by the view this table widget is rendered
            in.
        :type request: HttpRequest
        :param title: The title of the table. The title is displayed in the util header above the
            table if display_title is True.
        :type title: str
        :param display_title: Whether to display the title in the util header above the table.
        :type display_title: bool
        :param allow_global_search: Whether to display a global search field in the util header
            above the table.
        :type allow_global_search: bool
        :param allow_select: Whether to allow selecting rows in the table.
        :type allow_select: bool
        :param deselect_on_filter: Whether to deselect all selected filtered out rows when global
            or column search is applied.
        :type deselect_on_filter: bool
        :param allow_delete: Whether to allow deleting records from the table.
        :type allow_delete: bool
        :param delete_form: The form used to delete database records represented by the table rows.
            Only relevant if allow_delete is True.
        :type delete_form: :class:`BaCa2ModelForm`
        :param data_post_url: The url to which the data from the table delete form is posted. Only
            relevant if allow_delete is True.
        :type data_post_url: str
        :param paging: Paging options for the table. If not set, paging is disabled.
        :type paging: :class:`TableWidgetPaging`
        :param table_height: The height of the table in percent of the viewport height. If not set,
            the table height is not limited.
        :type table_height: int | None
        :param resizable_height: Whether to allow for dynamic resizing of the table height (through
            dragging a handle at the bottom of the table). Only relevant if table_height is set.
        :type resizable_height: bool
        :param link_format_string: A format string used to generate links for the table rows. The
        format string can reference the fields of database records represented by the table rows
        using double square brackets. For example, if the format string is '/records/[[id]]', the
        table rows will be linked to '/records/1', '/records/2', etc.
        :type link_format_string: str
        :param refresh_button: Whether to display a refresh button in the util header above the
            table. Refreshing the table will reload the data from the data source.
        :type refresh_button: bool
        :param refresh: Whether to automatically refresh the table data at a given interval.
        :type refresh: bool
        :param refresh_interval: The interval in seconds at which the table data is refreshed.
        :type refresh_interval: int
        :param default_sorting: Whether to use default sorting for the table.
        :type default_sorting: bool
        :param default_order_col: The name of the column to use for default ordering. If not set,
            the first column with sortable=True is used.
        :type default_order_col: str
        :param default_order_asc: Whether to use ascending or descending order for default
            ordering. If not set, ascending order is used.
        :type default_order_asc: bool
        :param stripe_rows: Whether to stripe the table rows.
        :type stripe_rows: bool
        :param highlight_rows_on_hover: Whether to highlight the table rows on mouse hover.
        :type highlight_rows_on_hover: bool
        :param hide_col_headers: Whether to hide the column headers.
        :type hide_col_headers: bool
        :param row_styling_rules: List of row styling rules. Each row styling rule defines a set of
            key-value pairs required for the row data to match the styling rule and a set of CSS
            styles to apply to the row if the row data matches the styling rule.
        :type row_styling_rules: List[:class:`RowStylingRule`]
        :param language: The language of the table. The language is used to set the DataTables
            language option. If not set, the language is set up from default django/user settings.
        :type language: str
        """
        super().__init__(name=name, request=request, widget_class='table-widget')

        self.title = title
        self.display_title = display_title
        self.allow_select = allow_select
        self.delete_form = delete_form
        self.data_post_url = data_post_url
        self.allow_delete = allow_delete
        self.allow_select = allow_select
        self.stripe_rows = stripe_rows
        self.highlight_rows_on_hover = highlight_rows_on_hover
        self.hide_col_headers = hide_col_headers
        self.cols = cols
        self.data_source = data_source
        self.allow_global_search = allow_global_search
        self.deselect_on_filter = deselect_on_filter
        self.link_format_string = link_format_string
        self.refresh_button = refresh_button
        self.paging = paging
        self.refresh = refresh
        self.refresh_interval = refresh_interval
        self.default_sorting = default_sorting
        self.default_order_asc = default_order_asc
        self.default_order_col = default_order_col
        self.table_height = table_height
        self.resizable_height = resizable_height
        self.row_styling_rules = row_styling_rules or []
        self.language_cdn = ''  # self.LOCALISATION.get(language)
        # TODO: Localisation overwrites our table styling. For now it's disabled. BWA-65

    @property
    def display_title(self) -> bool:
        """
        :return: Whether to display the title in the util header above the table.
        :rtype: bool
        """
        return self._display_title

    @display_title.setter
    def display_title(self, value: bool) -> None:
        """
        :param value: Whether to display the title in the util header above the table.
        :type value: bool
        """
        if not self.title:
            logger.warning('Table widget title must be set if display_title is True.')
        self._display_title = value

    @property
    def data_source(self) -> str | List[Dict[str, Any]]:
        """
        :return: Data source used to populate the table. If the table is used to display static
            data, the data source is a list of dictionaries representing table rows. If the table is
            used to display database records, the data source is the url of the view from which the
            table receives its data.
        :rtype: str | List[Dict[str, Any]]
        """
        return self._data_source

    @data_source.setter
    def data_source(self, value: str | List[Dict[str, Any]]) -> None:
        """
        :param value: Data source used to populate the table. If the table is used to display static
            data, the data source should be provided as a list of dictionaries representing table
            rows. The keys of the dictionaries should correspond to the names of the table columns.
            If the table is used to display database records, the data source should be set to the
            url of the view from which the table receives its data. The data source should return a
            JSON object containing a 'data' key with a list of dictionaries representing table rows.
            The keys of the dictionaries should correspond to the names of the table columns.
        :type value: str | List[Dict[str, Any]]
        """
        if isinstance(value, str):
            self._data_source = value
            self._data_source_url = value
            self._ajax = True
        else:
            self._data_source = value
            self._data_source_url = ''
            self._ajax = False

    @property
    def allow_delete(self) -> bool:
        """
        :return: Whether to allow deleting records from the table.
        :rtype: bool
        """
        return self._allow_delete

    @allow_delete.setter
    def allow_delete(self, value: bool) -> None:
        """
        :param value: Whether to allow deleting records from the table. If True, the delete_form and
            data_post_url must be set.
        :type value: bool
        """
        if value:
            if not self.delete_form:
                logger.warning('Table widget delete form must be set if allow_delete is True.')
            if not self.data_post_url:
                logger.warning('Table widget data post url must be set if allow_delete is True.')

        self._allow_delete = value

    @property
    def table_height(self) -> int | None:
        """
        :return: The height of the table in percent of the viewport height. None if the table height
            is not limited.
        :rtype: int | None
        """
        return self._table_height

    @table_height.setter
    def table_height(self, value: int | None) -> None:
        """
        :param value: The height of the table in percent of the viewport height. If set to None, the
            table height is not limited.
        :type value: int | None
        """
        if value is not None and (value < 0):
            raise ValueError('Table height cannot be negative')

        self._table_height = value

        if value is not None:
            self._limit_height = True
        else:
            self._limit_height = False

    @property
    def default_order_asc(self) -> bool:
        """
        :return: Whether to use ascending or descending order for default ordering.
        :rtype: bool
        """
        return self._default_order_asc

    @default_order_asc.setter
    def default_order_asc(self, value: bool) -> None:
        """
        :param value: Whether to use ascending or descending order for default ordering.
        :type value: bool
        """
        self._default_order_asc = value
        self._default_order = 'asc' if value else 'desc'

    @property
    def default_order_col(self) -> str:
        """
        :return: The name of the column to use for default ordering.
        :rtype: str
        """
        return self._default_order_col

    @default_order_col.setter
    def default_order_col(self, value: str | None) -> None:
        """
        :param value: The name of the column to use for default ordering. If set to None, the first
            column with sortable=True is used.
        :type value: str | None
        """
        if isinstance(value, str) and value not in [col.name for col in self.cols]:
            raise ValueError(f'Could not find column named: {value} in the table')
        self._default_order_col = value

    @property
    def _default_order_col_index(self) -> int:
        """
        :return: The index of the column to use for default ordering.
        :rtype: int
        :raises: Widget.ParameterError: If default sorting is enabled but no sortable column is
            found in the table.
        """
        if not self.default_sorting:
            return -1

        if self.default_order_col is None:
            try:
                return next(index for index, col in enumerate(self.cols)
                            if getattr(col, 'sortable'))
            except StopIteration:
                raise Widget.ParameterError('Default sorting is enabled but no sortable column '
                                            'found in the table')

        return next(index for index, col in enumerate(self.cols)
                    if getattr(col, 'name') == self.default_order_col)

    @property
    def _delete_button(self) -> bool:
        """
        :return: Whether to display the delete button in the util header above the table. The delete
            button is displayed if allow_delete is True and allow_select is True.
        :rtype: bool
        """
        return self.allow_delete and self.allow_select

    def _has_buttons(self) -> bool:
        """
        :return: Whether the util header above the table contains any buttons.
        :rtype: bool
        """
        return self._delete_button or self.refresh_button

    def _has_searchable_cols(self) -> bool:
        """
        :return: Whether the table contains any searchable columns.
        :rtype: bool
        """
        return any(col.searchable for col in self.cols)

    def _display_util_header(self) -> bool:
        """
        :return: Whether to display the util header above the table. The util header is displayed if
            the title is set, global search is enabled, or the util header contains any buttons.
        :rtype: bool
        """
        return self.display_title or self.allow_global_search or self._has_buttons()

    def _parse_static_data(self) -> None:
        """
        Parse static data source provided as a list of dictionaries representing table rows. The
        method ensures that all records have the same keys as the table columns and generates unique
        ids for the records if they do not contain an 'id' key.

        :raises: Widget.ParameterError: If the static data source is not a list of dictionaries.
        """
        assert isinstance(self._data_source, list), 'Static data source must be a list of dicts'

        for col in self.cols:
            for record in self._data_source:
                if col.name not in record:
                    record[col.name] = '---'

        for record in self._data_source:
            for key, value in record.items():
                if not str(value).strip():
                    record[key] = '---'
                if isinstance(value, Promise):
                    record[key] = str(value)

        for index, record in enumerate(self._data_source):
            if 'id' not in record:
                record['id'] = index

    def add_column(self, column: Column, index: int | None = None) -> None:
        """
        :param column: The column to add to the table.
        :type column: :class:`Column`
        :param index: The index at which to insert the column. If not set, the column is appended to
            the end of the columns list.
        :type index: int | None
        """
        if index is not None:
            self.cols.insert(index, column)
        else:
            self.cols.append(column)

    def add_columns(self, columns: List[Column], index: int | None = None) -> None:
        """
        :param columns: List of columns to add to the table.
        :type columns: List[:class:`Column`]
        :param index: The index at which to insert the columns. If not set, the columns are appended
            to the end of the columns list.
        :type index: int | None
        """
        for column in columns:
            self.add_column(column, index)

    def add_row_styling_rule(self, rule: RowStylingRule) -> None:
        """
        :param rule: The row styling rule to add to the table.
        :type rule: :class:`RowStylingRule`
        """
        self.row_styling_rules.append(rule)

    def build(self) -> Self:
        """
        Build the table widget. The method validates the widget parameters, sets the widget class,
        and prepares the widget context.

        :raises: Widget.ParameterError: If the title is not set and display_title is True, or if no
            searchable columns are found and global search is enabled.
        """
        if self.display_title and not self.title:
            raise Widget.ParameterError('Title must be set if display_title is True.')

        if self.allow_global_search and not self._has_searchable_cols():
            raise Widget.ParameterError('At least one column must be searchable if global '
                                        'search is enabled.')

        if self._ajax:
            self._data_source = []
        else:
            self._parse_static_data()

        if self.allow_select:
            self.cols.insert(0, SelectColumn())

        if self.allow_delete:
            self._build_delete_form_widget()
            self.cols.append(DeleteColumn())
        else:
            self.delete_form = None

        self.refresh_interval = self.refresh_interval * 1000
        self._table_height = f'{self.table_height}vh' if self._limit_height else ''
        self._build_widget_class()
        super().build()
        return self

    def _build_delete_form_widget(self) -> None:
        """
        Build the delete record form widget used to render the delete record form of the table
        widget if it allows for record deletion.

        :raises: Widget.ParameterError: If the delete_form or data_post_url is not set.
        """
        if not self.delete_form:
            raise self.ParameterError('Delete form must be set if allow_delete is True.')
        if not self.data_post_url:
            raise self.ParameterError('Data post url must be set if allow_delete is True.')

        self.delete_form = DeleteRecordFormWidget(
            request=self.request,
            form=self.delete_form,
            post_url=self.data_post_url,
            name=f'{self.name}_delete_record_form'
        ).get_context()

    def _build_widget_class(self) -> None:
        """
        Build the widget class used to apply CSS styling based on the widget parameters.
        """
        if self.stripe_rows:
            self.add_class('stripe')
        if self.highlight_rows_on_hover or self.link_format_string:
            self.add_class('row-hover')
        if self.link_format_string:
            self.add_class('link-records')
        if self.hide_col_headers:
            self.add_class('no-header')

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'display_util_header': self._display_util_header(),
            'display_title': self.display_title,
            'allow_global_search': self.allow_global_search,
            'deselect_on_filter': json.dumps(self.deselect_on_filter),
            'cols': [col.get_context() for col in self.cols],
            'has_buttons': self._has_buttons(),
            'has_length_menu': self.paging.allow_length_change if self.paging else False,
            'resizable_height': self.resizable_height,
            'table_height': self.table_height,
            'refresh_button': self.refresh_button,
            'allow_delete': self.allow_delete,
            'delete_button': self._delete_button,
            'delete_record_form_widget': self.delete_form,
            'localisation_cdn': self.language_cdn,
            'js_context': self.get_js_context()
        }

    def get_js_context(self) -> str:
        return json.dumps({
            'tableId': self.name,
            'ajax': self._ajax,
            'dataSourceUrl': self._data_source_url,
            'dataSource': self.data_source,
            'cols': [col.data_tables_context() for col in self.cols],
            'defaultSorting': self.default_sorting,
            'defaultOrder': self._default_order,
            'defaultOrderCol': self._default_order_col_index,
            'searching': self.allow_global_search,
            'paging': self.paging.get_context() if self.paging else False,
            'limitHeight': self._limit_height,
            'height': self.table_height,
            'refresh': self.refresh,
            'refreshInterval': self.refresh_interval,
            'linkFormatString': self.link_format_string,
            'rowStylingRules': [rule.get_context() for rule in self.row_styling_rules],
            'localisationCdn': self.language_cdn
        }, ensure_ascii=False)


class TableWidgetPaging:
    """
    Helper class for table widget used to define pagination options.
    """

    def __init__(self, *,
                 page_length: int = 10,
                 allow_length_change: bool = False,
                 length_change_options: List[int] = None,
                 deselect_on_page_change: bool = True) -> None:
        """
        :param page_length: The number of records to display per page.
        :type page_length: int
        :param allow_length_change: Whether to allow changing the number of records displayed per
            page.
        :type allow_length_change: bool
        :param length_change_options: List of options for the number of records displayed per page.
            If not set, the options are generated automatically based on the default page length.
        :type length_change_options: List[int]
        :param deselect_on_page_change: Whether to deselect all selected rows when changing the
            page. Only relevant if the table allows selecting rows.
        :type deselect_on_page_change: bool
        """
        self.page_length = page_length
        self.allow_length_change = allow_length_change
        self.deselect_on_page_change = deselect_on_page_change

        if not length_change_options:
            if page_length == 10:
                length_change_options = [10, 25, 50, -1]
            else:
                length_change_options = [page_length * i for i in range(1, 4)] + [-1]
        self.length_change_options = length_change_options

    def get_context(self) -> Dict[str, Any]:
        return {
            'page_length': self.page_length,
            'allow_length_change': self.allow_length_change,
            'length_change_options': self.length_change_options,
            'deselect_on_page_change': self.deselect_on_page_change
        }


class RowStylingRule:
    """
    Helper class for table widget used to define row styling rules. Used to apply custom CSS styles
    and/or add classes to table rows based on the row data matching specified mappings.
    """

    def __init__(self, *,
                 mappings: Dict[str, str | List[str]],
                 strict: bool = False,
                 styles: Dict[str, str] = None,
                 row_class: str = '') -> None:
        """
        :param mappings: Key-value pairs required for the row data to match the styling rule. The
            values can be strings or lists of strings. If the value is a string, the row data must
            have the key with the exact value. If the value is a list of strings, the row data must
            have the key with one of the values in the list.
        :type mappings: Dict[str, str | List[str]]
        :param strict: Whether to apply the styling rule only if all mappings are present in the row
            data. If False, the styling rule is applied if any of the mappings are present in the
            row data.
        :type strict: bool
        :param styles: CSS styles to apply to the row if the row data matches the styling rule.
            The keys of the dictionary should correspond to CSS style properties and the values to
            the CSS style values.
        :type styles: Dict[str, str]
        :param row_class: Class to add to the row if the row data matches the styling rule.
        :type row_class: str
        """
        self.mappings = mappings
        self.strict = strict
        self.styles = styles or {}
        self.row_class = row_class

    def get_context(self) -> Dict[str, Any]:
        if not self.styles and not self.row_class:
            raise ValueError('A row styling rule must have at least one style or class to apply.')

        return {
            'mappings': self.mappings,
            'strict': self.strict,
            'styles': self.styles,
            'row_class': self.row_class
        }


class DeleteRecordFormWidget(FormWidget):
    """
    Form widget class used to render a delete record form of the table widget if it allows for
    record deletion.
    """

    def __init__(self, *,
                 request: HttpRequest,
                 form: BaCa2ModelForm,
                 post_url: str,
                 name: str) -> None:
        """
        :param request: The HTTP request object received by the view this form widget's parent
            table widget is rendered in.
        :type request: HttpRequest
        :param form: The delete record form.
        :type form: :class:`BaCa2ModelForm`
        :param post_url: The url to which the form is posted. Should be the url of the model class
            view from which the table widget receives its data.
        :type post_url: str
        :param name: The name of the delete record form widget.
        :type name: str
        """
        super().__init__(request=request,
                         form=form,
                         post_target_url=post_url,
                         name=name,
                         submit_confirmation_popup=SubmitConfirmationPopup(
                             title=_('Confirm record deletion'),
                             message=_('Are you sure you want to delete this record')
                         ))
