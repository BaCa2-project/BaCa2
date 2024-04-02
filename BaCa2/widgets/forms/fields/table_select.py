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
                 table_widget_kwargs: dict = None,
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
        :param table_widget_kwargs: Additional keyword arguments to pass to the table widget
            constructor.
        :type table_widget_kwargs: dict
        :param kwargs: Additional keyword arguments to pass to the superclass constructor of the
            :class:`IntegerArrayField`.
        :type kwargs: dict
        """
        from widgets.listing import TableWidget

        table_widget_kwargs = {
            'name': table_widget_name,
            'title': label,
            'data_source': data_source_url,
            'cols': cols,
            'allow_column_search': allow_column_search,
            'allow_select': True,
            'deselect_on_filter': False,
            'highlight_rows_on_hover': True,
            'refresh_button': True
        } | (table_widget_kwargs or {})

        self.table_widget = TableWidget(**table_widget_kwargs).get_context()
        self.table_widget_id = table_widget_name
        self.data_source_url = data_source_url
        self.special_field_type = 'table_select'

        super().__init__(**kwargs)

    def widget_attrs(self, widget) -> dict:
        """
        Adds the class `table-select-field` and the data attribute `data-table-id` to the widget
        attributes. Required for the JavaScript and styling to work properly.
        """
        attrs = super().widget_attrs(widget)
        attrs['class'] = 'table-select-input'
        attrs['data-table-id'] = self.table_widget_id
        return attrs

    def __setattr__(self, key, value):
        """
        Overrides the default __setattr__ method to update table widget data source url when the
        `data_source_url` attribute is set. If the `initial` attribute is set as a list,it is
        converted to a comma-separated string of primary keys.

        :raises ValueError: If the `initial` attribute is set as a list of non-integer values or
            as a non-string, non-list value.
        """
        if key == 'data_source_url':
            self.table_widget['data_source_url'] = value
        if key == 'initial' and value is not None:
            if isinstance(value, list):
                if not isinstance(value[0], int):
                    raise ValueError('The initial value of a TableSelectField must be a list of '
                                     'integers (primary keys) or a comma-separated string of '
                                     'integers.')
                value = ','.join(str(pk) for pk in value)
            elif not isinstance(value, str):
                raise ValueError('The initial value of a TableSelectField must be a list of '
                                 'integers (primary keys) or a comma-separated string of integers.')

        super().__setattr__(key, value)

    @staticmethod
    def parse_value(value: str) -> List[int]:
        """
        :param value: The field value as a comma-separated string of primary keys.
        :type value: str
        :return: The field value as a list of integers.
        :rtype: List[int]
        """
        return [int(pk) for pk in value.split(',')] if value else []
