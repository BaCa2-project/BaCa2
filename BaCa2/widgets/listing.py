from typing import List
from django.db import models
from django.db.models.query import QuerySet


class Record:
    def __init__(self,
                 model: models.Model,
                 fields: List[str],
                 fields_type: dict = None,
                 fields_style: dict = None
                 ):
        self.fields = []
        for field in fields:
            self.fields.append([getattr(model, field), 1])


class Table:
    def __init__(self,
                 queryset: QuerySet,
                 cols: List[str],
                 header: dict = None,
                 cols_type: dict = None,
                 cols_style: dict = None,
                 sort_by: str = None,
                 sort_order: str = 'desc'
                 ):
        self.cols = cols

        if header:
            self.header = header
        else:
            self.header = {}
        for col in cols:
            if col not in self.header:
                self.header[col] = col

        if cols_style:
            self.cols_style = cols_style
        else:
            self.cols_style = {}

        self.records = []
        for i in queryset:
            self.records.append(Record(i, self.cols, cols_type))

    def get_context(self) -> dict:
        context = {
            'cols_num': len(self.cols),
            'records_num': len(self.records),
            'cols': self.cols,
            'header': [self.header[_] for _ in self.cols],
            'records': self.records
        }

        return context
