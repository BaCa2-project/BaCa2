from enum import Enum

from widgets.base import Widget


class Attachment(Widget):
    """
    Widget that representing a resource that can be downloaded or viewed. Renders to a small
    button-like element that links to the resource.
    """

    class ResourceType(Enum):
        """
        Enum representing the type of resource the attachment links to.
        """
        PAGE = 'page'
        FILE = 'file'

    class ContentType(Enum):
        """
        Enum representing the type of content the attachment links to. This is used to determine
        the icon displayed next to the attachment (if no icon is specified explicitly).
        """
        UNSPECIFIED_PAGE = 'unspecified_page', 'box-arrow-up-right'
        UNSPECIFIED_FILE = 'unspecified_file', 'download'

    def __init__(self, *,
                 name: str,
                 link: str,
                 title: str = '',
                 download_name: str = '',
                 icon: str = '',
                 source_type: 'ResourceType' = None,
                 content_type: 'ContentType' = None) -> None:
        """
        :param name: Name of the attachment. Unique within view context scope.
        :type name: str
        :param link: URL of the resource the attachment links to.
        :type link: str
        :param title: Title of the attachment. Displayed on the button.
        :type title: str
        :param download_name: Name of the downloaded file. If not specified, the title is used.
            Only relevant for file resources.
        :type download_name: str
        :param icon: Name of the icon to display next to the attachment. If not specified, the
            icon is determined based on the content type.
        :type icon: str
        :param source_type: Type of resource the attachment links to. Defaults to
            `ResourceType.FILE` if not specified.
        :type source_type: :class:`Attachment.ResourceType`
        :param content_type: Type of content the attachment links to. Defaults to unspecified
            page/file if not specified.
        :type content_type: :class:`Attachment.ContentType`
        """
        super().__init__(name=name)
        self.widget_class = 'attachment btn btn-sm btn-outline-light_muted'
        self.link = link
        self.title = title
        self.download_name = download_name
        self.source_type = source_type
        self.content_type = content_type
        self.icon = icon

    def build(self) -> None:
        self.title = self.title or self.name
        self.download_name = self.download_name or self.title
        self.source_type = self.source_type or self.ResourceType.FILE

        if not self.content_type:
            if self.source_type == self.ResourceType.PAGE:
                self.content_type = self.ContentType.UNSPECIFIED_PAGE
            else:
                self.content_type = self.ContentType.UNSPECIFIED_FILE

        if not self.icon:
            self.icon = self.content_type.value[1]

        super().build()

    def get_context(self) -> dict:
        return super().get_context() | {
            'link': self.link,
            'title': self.title,
            'download_name': self.download_name,
            'source_type': self.source_type.value,
            'content_type': self.content_type.value[0],
            'icon': self.icon
        }
