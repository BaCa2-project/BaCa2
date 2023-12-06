from __future__ import annotations

from typing import (List, Dict, TypeVar, Type, Any)
from django.db import models
import json

from widgets.base import Widget
from widgets.listing.columns import Column, SelectColumn, DeleteColumn

T = TypeVar('T', bound=models.Model)


class TableWidget(Widget):
    def __init__(self,
                 model_cls: Type[T],
                 cols: List[Column],
                 allow_select: bool = False,
                 allow_delete: bool = False,
                 name: str = '',
                 paging: TableWidgetPaging = None,
                 refresh: bool = False,
                 refresh_interval: int = 30,
                 default_order_col: str = '',
                 default_order_asc: bool = True,
                 stripe_rows: bool = True) -> None:
        model_name = model_cls.__name__.lower()
        name = name if name else f'{model_name}_table_widget'

        super().__init__(name)

        if not default_order_col:
            default_order_col = next(col.name for col in cols if getattr(col, 'sortable'))

        if allow_select:
            cols.insert(0, SelectColumn())
        if allow_delete:
            cols.append(DeleteColumn())

        self.model_cls = model_cls
        self.model_name = model_name
        self.cols = cols
        self.paging = paging
        self.refresh = refresh
        self.refresh_interval = refresh_interval * 1000
        self.default_order = 'asc' if default_order_asc else 'desc'
        self.table_class = 'stripe' if stripe_rows else ''

        try:
            self.default_order_col = next(index for index, col in enumerate(cols)
                                          if getattr(col, 'name') == default_order_col)
        except StopIteration:
            raise ValueError(f'Column {default_order_col} not found in table {name}')

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {
            'model_cls': self.model_cls,
            'model_name': self.model_name,
            'cols': [col.get_context() for col in self.cols],
            'cols_num': len(self.cols),
            'paging': self.paging.get_context() if self.paging else json.dumps(False),
            'refresh': json.dumps(self.refresh),
            'refresh_interval': self.refresh_interval,
            'table_class': self.table_class,
            'default_order_col': self.default_order_col,
            'default_order': self.default_order
        }


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
