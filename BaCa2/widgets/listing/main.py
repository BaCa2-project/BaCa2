from typing import List

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from widgets.forms.main import DeleteAnnouncementForm
from widgets.listing import TableWidget, TableWidgetPaging
from widgets.listing.columns import Column, TextColumn


class AnnouncementsTable(TableWidget):
    def __init__(self,
                 request: HttpRequest | None = None,
                 cols: List[Column] | None = None,
                 allow_select: bool = True,
                 allow_delete: bool = True,
                 record_links: bool = True,
                 **kwargs) -> None:
        from main.views import AnnouncementModelView

        if not cols:
            cols = [TextColumn(name='title', header=_('Title'), searchable=True),
                    TextColumn(name='content', header=_('Content'), searchable=True),
                    TextColumn(name='f_date', header=_('Announcement date'), searchable=True)]

        if allow_delete:
            delete_form = DeleteAnnouncementForm()
            data_post_url = AnnouncementModelView.post_url()
        else:
            delete_form = None
            data_post_url = ''

        if record_links:
            kwargs['link_format_string'] = '/announcement/[[id]]'

        if 'paging' not in kwargs:
            kwargs['paging'] = TableWidgetPaging()

        if 'data_source' not in kwargs:
            kwargs['data_source'] = AnnouncementModelView.get_url(
                mode=AnnouncementModelView.GetMode.ALL
            )

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
