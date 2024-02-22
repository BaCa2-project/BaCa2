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

        self.special_field_type = 'table_select'
        self.data_source_url = data_source_url
        table_widget = TableWidget(
            name=table_widget_name,
            title=label,
            data_source=data_source_url,
            cols=cols,
            allow_column_search=allow_column_search,
            allow_select=True,
            deselect_on_filter=False,
            highlight_rows_on_hover=True,
        )
        self.table_widget = table_widget.get_context()
        self.table_widget_id = table_widget_name

        super().__init__(**kwargs)

    def update_data_source_url(self, data_source_url: str) -> None:
        """
        Updates the data source url of the field's table widget.

        :param data_source_url: The new data source url.
        :type data_source_url: str
        """
        self.data_source_url = data_source_url
        self.table_widget['data_source_url'] = data_source_url

    def widget_attrs(self, widget) -> dict:
        """
        Adds the class `table-select-field` and the data attribute `data-table-id` to the widget
        attributes. Required for the JavaScript and styling to work properly.
        """
        attrs = super().widget_attrs(widget)
        attrs['class'] = 'table-select-field'
        attrs['data-table-id'] = self.table_widget_id
        return attrs

    @staticmethod
    def parse_value(value: str) -> List[int]:
        """
        :param value: The field value as a comma-separated string of primary keys.
        :type value: str
        :return: The field value as a list of integers.
        :rtype: List[int]
        """
        return [int(pk) for pk in value.split(',')] if value else []
