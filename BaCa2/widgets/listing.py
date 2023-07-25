from typing import List, Dict
from django.db import models
from django.db.models.query import QuerySet


class Record:
    def __init__(self,
                 model: models.Model,
                 fields: List[str],
                 labels: Dict[str, str]) -> None:
        self.fields = []
        for field in fields:
            self.fields.append([getattr(model, field), labels[field]])


class Table:
    def __init__(self,
                 queryset: QuerySet,
                 cols: List[str],
                 header: Dict[str, str] = None,
                 sortable: bool = False,
                 searchable: bool = False) -> None:
        self.cols = cols

        if header:
            self.header = header
        else:
            self.header = {}
        for col in cols:
            if col not in self.header:
                self.header[col] = col

        self.records = []
        for model in queryset:
            self.records.append(Record(model=model,
                                       fields=self.cols,
                                       labels=self.header))

        self.sortable = sortable
        self.searchable = searchable

    def get_context(self) -> dict:
        context = {
            'cols_num': len(self.cols),
            'records_num': len(self.records),
            'cols': self.cols,
            'header': [self.header[_] for _ in self.cols],
            'records': self.records,
            'sortable': self.sortable,
            'searchable': self.searchable,
            'class': "",
        }

        if self.sortable:
            context['class'] += "table-sortable"
        if self.searchable:
            context['class'] += " table-searchable"

        return context
