from __future__ import annotations

import json
from typing import (List, Dict, Any)

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from widgets.listing.columns import Column, SelectColumn, DeleteColumn
from widgets.listing.data_sources import TableDataSource
from widgets.forms import BaCa2ModelForm, FormWidget
from widgets.popups.forms import SubmitConfirmationPopup
from widgets.forms.course import DeleteCourseForm
from main.models import Course


class TableWidget(Widget):
    delete_forms = {
        Course: DeleteCourseForm
    }

    def __init__(self,
                 request: HttpRequest,
                 data_source: TableDataSource,
                 cols: List[Column],
                 title: str = '',
                 display_title: bool = True,
                 allow_global_search: bool = True,
                 allow_column_search: bool = True,
                 allow_select: bool = False,
                 allow_delete: bool = False,
                 name: str = '',
                 paging: TableWidgetPaging = None,
                 refresh_button: bool = False,
                 refresh: bool = False,
                 refresh_interval: int = 30,
                 default_order_col: str = '',
                 default_order_asc: bool = True,
                 stripe_rows: bool = True) -> None:
        if not name:
            name = data_source.generate_table_widget_name()

        super().__init__(name=name, request=request)

        if not title:
            title = data_source.generate_table_widget_title()
        self.title = title
        self.display_title = display_title

        if not default_order_col:
            default_order_col = next(col.name for col in cols if getattr(col, 'sortable'))

        if allow_select:
            cols.insert(0, SelectColumn())

        if allow_delete:
            model = getattr(data_source, 'model', None)

            if not model:
                raise ValueError('Data source has to be a ModelDataSource to allow delete.')
            if model not in TableWidget.delete_forms.keys():
                raise ValueError(f'No delete form found for model {model}.')

            delete_record_form_widget = DeleteRecordFormWidget(
                request=request,
                form=TableWidget.delete_forms[model](),
                post_url=data_source.get_url(),
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

        for col in cols:
            col.request = request
        self.cols = cols

        self.allow_global_search = allow_global_search
        self.allow_column_search = allow_column_search
        self.refresh_button = refresh_button
        self.data_source = data_source
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
            raise ValueError(f'Column {default_order_col} not found in table {name}')

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'title': self.title,
            'display_util_header': self.display_util_header(),
            'display_title': self.display_title,
            'allow_global_search': json.dumps(self.allow_global_search),
            'allow_column_search': self.allow_column_search,
            'data_source_url': self.data_source.get_url(),
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
        return self.display_title or self.table_buttons or self.allow_global_search


class TableWidgetPaging:
    def __init__(self,
                 page_length: int = 10,
                 allow_length_change: bool = False,
                 length_change_options: List[int] = None,
                 deselect_on_page_change: bool = True) -> None:
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
    def __init__(self,
                 request: HttpRequest,
                 form: BaCa2ModelForm,
                 post_url: str,
                 name: str) -> None:
        super().__init__(request=request,
                         form=form,
                         post_target=post_url,
                         name=name,
                         submit_confirmation_popup=SubmitConfirmationPopup(
                             title=_("Confirm record deletion"),
                             message=_("Are you sure you want to delete this record")
                         ))
