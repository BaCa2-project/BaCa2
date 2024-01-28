from __future__ import annotations

import json
from typing import (List, Dict, Any)

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from widgets.listing.columns import Column, SelectColumn, DeleteColumn
from widgets.forms import BaCa2ModelForm, FormWidget
from widgets.popups.forms import SubmitConfirmationPopup


class TableWidget(Widget):
    """
    Widget used to display a table of data. Constructor arguments define the table's properties
    such as title, columns, data source url, search options, etc.

    The table widget is rendered with the help of the DataTables jQuery plugin using the
    `templates/widget_templates/table.html` template.

    All table widgets use AJAX get requests to fetch the table data from the data source url.
    The data source url should return a JSON object containing a 'data' key with a list of
    dictionaries representing table rows. The keys of the dictionaries should correspond to the
    names of the table columns.

    See also:
        - :class:`Column`
        - :class:`TableWidgetPaging`
        - :class:`Widget`
    """

    def __init__(self,
                 name: str,
                 data_source_url: str,
                 cols: List[Column],
                 request: HttpRequest | None = None,
                 title: str = '',
                 display_title: bool = True,
                 allow_global_search: bool = True,
                 allow_column_search: bool = True,
                 allow_select: bool = False,
                 deselect_on_filter: bool = True,
                 allow_delete: bool = False,
                 delete_form: BaCa2ModelForm = None,
                 paging: TableWidgetPaging = None,
                 refresh_button: bool = False,
                 refresh: bool = False,
                 refresh_interval: int = 30,
                 default_order_col: str = '',
                 default_order_asc: bool = True,
                 stripe_rows: bool = True,
                 highlight_rows_on_hover: bool = False) -> None:
        """
        :param name: The name of the table widget. Names are used as ids for the HTML <table>
            elements of the rendered table widgets.
        :type name: str
        :param data_source_url: The url from which the table data is fetched via AJAX get request.
        The url should return a JSON object containing a 'data' key with a list of dictionaries
        representing table rows. The keys of the dictionaries should correspond to the names of
        the table columns.
        :type data_source_url: str
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
        :param allow_column_search: Whether to display a search field for each searchable column.
        :type allow_column_search: bool
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
        :param paging: Paging options for the table. If not set, paging is disabled.
        :type paging: :class:`TableWidgetPaging`
        :param refresh_button: Whether to display a refresh button in the util header above the
            table. Refreshing the table will reload the data from the data source.
        :type refresh_button: bool
        :param refresh: Whether to automatically refresh the table data at a given interval.
        :type refresh: bool
        :param refresh_interval: The interval in seconds at which the table data is refreshed.
        :type refresh_interval: int
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
        """
        super().__init__(name=name, request=request)

        if display_title and not title:
            raise Widget.WidgetParameterError('Title must be set if display_title is True.')

        self.title = title
        self.display_title = display_title

        if not default_order_col:
            default_order_col = next(col.name for col in cols if getattr(col, 'sortable'))

        if allow_select:
            cols.insert(0, SelectColumn())

        if allow_delete:
            if not delete_form:
                raise Widget.WidgetParameterError('Delete form must be set if allow_delete is '
                                                  'True.')

            delete_record_form_widget = DeleteRecordFormWidget(
                request=request,
                form=delete_form,
                post_url=data_source_url,
                name=f'{name}_delete_record_form'
            )
            cols.append(DeleteColumn())
        else:
            delete_record_form_widget = None
        self.allow_delete = allow_delete
        self.delete_record_form_widget = delete_record_form_widget

        if allow_select and allow_delete:
            self.delete_button = True
        else:
            self.delete_button = False

        if stripe_rows:
            self.add_class('stripe')
        if highlight_rows_on_hover:
            self.add_class('row-hover')

        for col in cols:
            col.request = request
        self.cols = cols

        self.allow_global_search = allow_global_search
        self.allow_column_search = allow_column_search
        self.deselect_on_filter = deselect_on_filter
        self.refresh_button = refresh_button
        self.data_source_url = data_source_url
        self.paging = paging
        self.refresh = refresh
        self.refresh_interval = refresh_interval * 1000
        self.default_order = 'asc' if default_order_asc else 'desc'

        if self.delete_button or self.refresh_button:
            self.table_buttons = True
        else:
            self.table_buttons = False

        try:
            self.default_order_col = next(index for index, col in enumerate(cols)
                                          if getattr(col, 'name') == default_order_col)
        except StopIteration:
            raise Widget.WidgetParameterError(f'Column {default_order_col} not found in table '
                                              f'{name}')

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'display_util_header': self.display_util_header(),
            'display_title': self.display_title,
            'allow_global_search': json.dumps(self.allow_global_search),
            'allow_column_search': self.allow_column_search,
            'deselect_on_filter': json.dumps(self.deselect_on_filter),
            'data_source_url': self.data_source_url,
            'cols': [col.get_context() for col in self.cols],
            'cols_num': len(self.cols),
            'table_buttons': self.table_buttons,
            'paging': self.paging.get_context() if self.paging else json.dumps(False),
            'refresh': json.dumps(self.refresh),
            'refresh_interval': self.refresh_interval,
            'refresh_button': json.dumps(self.refresh_button),
            'default_order_col': self.default_order_col,
            'default_order': self.default_order,
            'allow_delete': self.allow_delete,
            'delete_button': self.delete_button,
            'delete_record_form_widget': self.delete_record_form_widget.get_context()
            if self.delete_record_form_widget else None
        }

    def display_util_header(self) -> bool:
        """
        Returns whether to display the util header above the table depending on the table's
        properties.

        :return: Whether to display the util header above the table.
        :rtype: bool
        """
        return self.display_title or self.table_buttons or self.allow_global_search


class TableWidgetPaging:
    """
    Helper class for table widget used to define paging options.

    See also:
        - :class:`TableWidget`
    """
    def __init__(self,
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
            'allow_length_change': json.dumps(self.allow_length_change),
            'length_change_options': self.length_change_options,
            'deselect_on_page_change': json.dumps(self.deselect_on_page_change)
        }


class DeleteRecordFormWidget(FormWidget):
    """
    Form widget class used to render a delete record form of the table widget if it allows for
    record deletion.

    See also:
        - :class:`TableWidget`
        - :class:`FormWidget`
    """
    def __init__(self,
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
                         post_target=post_url,
                         name=name,
                         submit_confirmation_popup=SubmitConfirmationPopup(
                             title=_("Confirm record deletion"),
                             message=_("Are you sure you want to delete this record")
                         ))
