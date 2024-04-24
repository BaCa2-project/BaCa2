from enum import Enum

from widgets.base import Widget


class Attachment(Widget):
    class SourceType(Enum):
        PAGE = 'page'
        FILE = 'file'

    class ContentType(Enum):
        UNSPECIFIED_PAGE = 'unspecified_page', 'bi bi-box-arrow-up-right'
        UNSPECIFIED_FILE = 'unspecified_file', 'bi bi-download'

    def __init__(self, *,
                 name: str,
                 link: str,
                 title: str = '',
                 download_name: str = '',
                 source_type: 'Attachment.SourceType' = None,
                 content_type: 'Attachment.ContentType' = None) -> None:
        super().__init__(name=name)
        self.link = link

        if not title:
            title = name
        self.title = title

        if not download_name:
            download_name = title
        self.download_name = download_name

        if not source_type:
            source_type = self.SourceType.FILE
        self.source_type = source_type

        if not content_type:
            if source_type == self.SourceType.PAGE:
                content_type = self.ContentType.UNSPECIFIED_PAGE
            else:
                content_type = self.ContentType.UNSPECIFIED_FILE

        self.content_type = content_type
        self.icon = content_type.value[1]

    def get_context(self) -> dict:
        return super().get_context() | {
            'link': self.link,
            'title': self.title,
            'download_name': self.download_name,
            'source_type': self.source_type.value,
            'content_type': self.content_type.value[0],
            'icon': self.icon
        }
