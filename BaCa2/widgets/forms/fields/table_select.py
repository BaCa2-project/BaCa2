from __future__ import annotations

from typing import List

from widgets.forms.fields import IntegerArrayField
from widgets.listing.columns import Column


class TableSelectField(IntegerArrayField):
    """
    A field that allows the user to select multiple items from a table. The field value is posted
    as an array of comma-separated primary keys of the selected records.

    See also:
    - :class:`IntegerArrayField`
    """
    def __init__(self,
                 label: str,
                 table_widget_name: str,
                 data_source_url: str,
                 cols: List[Column],
                 allow_column_search: bool = True,
                 **kwargs) -> None:
        """
        :param label: The label of the field. Will appear as the title of the table widget.
        :type label: str
        :param table_widget_name: The name of the table widget used by this field.
        :type table_widget_name: str
        :param data_source: The data source url for the table widget.
        :type data_source: str
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
        self.data_source_url = data_source_url
        table_widget = TableWidget(
            name=table_widget_name,
            title=label,
            data_source_url=data_source_url,
            cols=cols,
            allow_column_search=allow_column_search,
            allow_select=True,
            deselect_on_filter=False,
        )
        self.table_widget = table_widget.get_context()
