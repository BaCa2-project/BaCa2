from typing import List

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from widgets.forms.main import DeleteAnnouncementForm
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.columns import Column, DatetimeColumn, TextColumn


class AnnouncementsTable(TableWidget):
    """
    Table widget for displaying announcement data in the admin panel. To render announcements for
    users use the :class:`widgets.notification.AnnouncementBlock` widget.
    """

    def __init__(self,
                 request: HttpRequest | None = None,
                 cols: List[Column] | None = None,
                 allow_select: bool = True,
                 allow_delete: bool = True,
                 record_links: bool = True,
                 **kwargs) -> None:
        """
        :param request: The request object received by the view this widget is rendered in.
        :type request: HttpRequest
        :param cols: A list of columns to display in the table. If not provided, the default columns
            are used (title, content, formatted date).
        :type cols: List[Column]
        :param allow_select: Whether to display checkboxes for selecting rows in the table.
        :type allow_select: bool
        :param allow_delete: Whether to display a delete button for deleting records.
        :type allow_delete: bool
        :param record_links: Whether to link table rows to announcement edit views for the
            corresponding records.
        :type record_links: bool
        :param kwargs: Additional keyword arguments to pass to the parent constructor.
        """
        from main.views import AnnouncementModelView

        if not cols:
            cols = [TextColumn(name='title', header=_('Title'), searchable=True),
                    DatetimeColumn(name='date', header=_('Announcement date'), searchable=True),
                    TextColumn(name='course', header=_('Course'), searchable=True)]

        if allow_delete:
            delete_form = DeleteAnnouncementForm()
            data_post_url = AnnouncementModelView.post_url()
        else:
            delete_form = None
            data_post_url = ''

        if record_links:
            kwargs['link_format_string'] = '/main/announcement/[[id]]/'

        if 'paging' not in kwargs:
            kwargs['paging'] = TableWidgetPaging()

        if 'data_source' not in kwargs:
            kwargs['data_source'] = AnnouncementModelView.get_url(
                mode=AnnouncementModelView.GetMode.ALL
            )

        if 'table_height' not in kwargs:
            kwargs['table_height'] = 50

        super().__init__(
            name='announcements_table_widget',
            request=request,
            title=_('Announcements'),
            data_post_url=data_post_url,
            delete_form=delete_form,
            cols=cols,
            allow_select=allow_select,
            allow_delete=allow_delete,
            **kwargs
        )
