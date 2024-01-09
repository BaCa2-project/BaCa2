from __future__ import annotations

from typing import List

from widgets.forms.fields import IntegerArrayField
from widgets.listing.columns import Column
from widgets.listing.data_sources import TableDataSource


class TableSelectField(IntegerArrayField):
    """
    A field that allows the user to select multiple items from a table. The field value is posted
    as an array of comma-separated primary keys of the selected records.

    See also:
    - :class:`IntegerArrayField`
    """
    def __init__(self,
                 label: str,
                 data_source: TableDataSource,
                 cols: List[Column],
                 allow_column_search: bool = True,
                 **kwargs) -> None:
        """
        :param label: The label of the field. Will appear as the title of the table widget.
        :type label: str
        :param data_source: The data source for the table widget.
        :type data_source: TableDataSource
        :param cols: The columns to display in the table widget.
        :type cols: List[Column]
        :param allow_column_search: Whether to display separate search fields for each searchable
            column.
        :type allow_column_search: bool
        :param kwargs: Additional keyword arguments to pass to the superclass constructor of the
            :class:`IntegerArrayField`.
        :type kwargs: dict
        """
        from widgets.listing import TableWidget

        super().__init__(**kwargs)
        self.widget.attrs.update({'class': 'table-select-field'})
        self.data_source = data_source
        table_widget = TableWidget(
            title=label,
            data_source=data_source,
            cols=cols,
            allow_column_search=allow_column_search,
            allow_select=True,
            deselect_on_filter=False,
        )
        table_widget.name = 'field_' + table_widget.name
        self.table_widget = table_widget.get_context()