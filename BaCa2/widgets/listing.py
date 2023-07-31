from typing import List, Dict, TypeVar, Type
from django.db import models

T = TypeVar('T', bound=models.Model)


class Table:
    def __init__(self,
                 model_cls: Type[T],
                 table_id: str = "",
                 cols: List[str] = None,
                 header: Dict[str, str] = None,
                 paging: bool = False,
                 page_length: int = 10,
                 length_change: bool = False,
                 length_menu: List[int] = None,
                 refresh: bool = False,
                 refresh_interval: int = 30000, ) -> None:
        self.model_cls = model_cls
        self.paging = paging
        self.page_length = page_length
        self.length_change = length_change
        self.refresh = refresh
        self.refresh_interval = refresh_interval

        if table_id:
            self.table_id = table_id
        else:
            self.table_id = f'{model_cls.__name__.lower()}-table'

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

    def get_context(self) -> dict:
        context = {
            'table_id': self.table_id,
            'model_cls': self.model_cls,
            'cols': self.cols,
            'header': [self.header[_] for _ in self.cols],
            'cols_num': len(self.cols),
            'paging': self.paging,
            'page_length': self.page_length,
            'length_change': self.length_change,
            'length_menu': self.length_menu,
            'refresh': self.refresh,
            'refresh_interval': self.refresh_interval,
        }

        return context
