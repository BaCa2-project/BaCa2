from typing import List, Dict, TypeVar, Type
from django.db import models

import json

T = TypeVar('T', bound=models.Model)


class TableWidget:
    ACCESS_MODES = ['user', 'admin']
    RECORD_METHODS = ['details', 'edit', 'delete', 'select']

    class AccessModeError(Exception):
        pass

    def __init__(self,
                 model_cls: Type[T],
                 access_mode: str = 'user',
                 table_id: str = '',
                 cols: List[str] = None,
                 header: Dict[str, str] = None,
                 paging: bool = False,
                 page_length: int = 10,
                 length_change: bool = False,
                 length_menu: List[int] = None,
                 refresh: bool = False,
                 refresh_interval: int = 30000,
                 style: str = "",
                 stripe: bool = True,
                 default_order_col: str = '',
                 default_order_asc: bool = True,
                 create: bool = False,
                 details: bool = False,
                 edit: bool = False,
                 delete: bool = False,
                 select: bool = False,
                 non_sortable: List[str] or 'all' = None) -> None:
        self.model_cls = model_cls
        self.model_name = model_cls.__name__.lower()
        self.paging = paging
        self.page_length = page_length
        self.length_change = length_change
        self.refresh = refresh
        self.refresh_interval = refresh_interval
        self.record_methods = {method: {'on': 'false', 'col_index': -1} for method in TableWidget.RECORD_METHODS}

        if default_order_asc:
            self.default_order = 'asc'
        else:
            self.default_order = 'desc'

        if access_mode not in TableWidget.ACCESS_MODES:
            raise TableWidget.AccessModeError('Access mode not recognized.')
        else:
            self.access_mode = access_mode

        self.table_class = ''
        if style:
            self.table_class += style + ' '
        if stripe:
            self.table_class += 'stripe '

        if table_id:
            self.table_id = table_id
        else:
            self.table_id = f'{self.model_name}-table'

        if cols:
            self.cols = cols
        else:
            self.cols = [field.name for field in model_cls._meta.fields]

        if header:
            self.header = header
        else:
            self.header = {}
        for col in self.cols:
            if col not in self.header:
                self.header[col] = col

        if length_menu:
            self.length_menu = length_menu
        elif self.page_length == 10:
            self.length_menu = [10, 25, 50, -1]
        else:
            self.length_menu = [self.page_length * i for i in range(1, 4)] + [-1]

        if not non_sortable:
            self.non_sortable = []
        else:
            self.non_sortable = non_sortable

        if select:
            self._add_record_method('select', col_index=0)
        if details:
            self._add_record_method('details', col_index=None)
        if edit:
            self._add_record_method('edit')
        if delete:
            self._add_record_method('delete')

        if non_sortable == 'all':
            self.non_sortable_indexes = [i for i in range(len(cols))]
        else:
            self.non_sortable_indexes = [self.cols.index(col) for col in self.non_sortable]

        if not default_order_col:
            if select:
                default_order_col = self.cols[1]
            else:
                default_order_col = self.cols[0]
        self.default_order_col = self.cols.index(default_order_col)

    def _add_record_method(self, name: str, header: str = '', col_index: int or None = -1):
        if col_index is not None:
            if col_index == -1:
                self.cols.append(name)
                self.record_methods[name]['col_index'] = self.cols.index(name)
            else:
                self.cols.insert(col_index, name)
                for method in self.record_methods.keys():
                    if self.record_methods[method]['col_index'] >= col_index:
                        self.record_methods[method]['col_index'] += 1
                self.record_methods[name]['col_index'] = self.cols.index(name)

            self.header[name] = header
            self.non_sortable.append(name)

        self.record_methods[name]['on'] = 'true'

    def get_context(self) -> dict:
        context = {
            'table_id': self.table_id,
            'model_cls': self.model_cls,
            'access_mode': self.access_mode,
            'model_name': self.model_name,
            'cols': self.cols,
            'header': self.header,
            'cols_num': len(self.cols),
            'paging': json.dumps(self.paging),
            'page_length': self.page_length,
            'length_change': json.dumps(self.length_change),
            'length_menu': self.length_menu,
            'refresh': json.dumps(self.refresh),
            'refresh_interval': self.refresh_interval,
            'table_class': self.table_class,
            'non_sortable_indexes': self.non_sortable_indexes,
            'default_order_col': self.default_order_col,
            'default_order': self.default_order,
            'record_methods': self.record_methods
        }

        return context
