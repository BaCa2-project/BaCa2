from typing import List

from main.models import Announcement as AnnouncementModel
from widgets.base import Widget


class Announcement(Widget):
    """
    A widget displaying an announcement. It contains the title, content, and date of the
    announcement (if not hidden).
    """

    def __init__(self,
                 name: str,
                 announcement: AnnouncementModel,
                 display_date: bool = True,
                 display_time: bool = True):
        """
        :param name: Name of the widget.
        :type name: str
        :param announcement: Announcement to display.
        :type announcement: Announcement
        :param display_date: Whether to display the date of the announcement.
        :type display_date: bool
        :param display_time: Whether to display the time of the announcement. Only relevant if
            display_date is True.
        :type display_time: bool
        """
        super().__init__(name=name)
        self.announcement = announcement
        self.display_date = display_date
        self.date_format = '%Y-%m-%d'

        if display_time:
            self.date_format += ' %H:%M'

    def get_context(self) -> dict:
        return super().get_context() | {
            'title': self.announcement.title,
            'content': self.announcement.content,
            'display_date': self.display_date,
            'date': self.announcement.date.strftime(self.date_format),
        }


class AnnouncementBlock(Widget):
    """
    A widget displaying a block of announcements. It contains a list of Announcement widgets.
    """

    def __init__(self,
                 name: str,
                 announcements: List[AnnouncementModel] | List[Announcement],
                 display_date: bool = True,
                 display_time: bool = True):
        """
        :param name: Name of the widget.
        :type name: str
        :param announcements: Announcements to display. Can be a list of models or announcement
            widgets. If models are provided, a list of widgets will be automatically created using
            the block widget parameters.
        :type announcements: List[main.models.Announcement] | List[Announcement]
        :param display_date: Whether to display the date of the announcements. Only relevant if
            the announcements are passed as models.
        :type display_date: bool
        :param display_time: Whether to display the time of the announcements. Only relevant if
            the announcements are passed as models.
        :type display_time: bool
        """
        super().__init__(name=name)

        if not announcements:
            self.announcements = []
            return

        if isinstance(announcements[0], Announcement):
            self.announcements = announcements
        else:
            self.announcements = [
                Announcement(name=f'{a.title}-{a.id}',
                             announcement=a,
                             display_date=display_date,
                             display_time=display_time)
                for a in announcements
            ]

    def get_context(self) -> dict:
        return super().get_context() | {
            'announcements': [a.get_context() for a in self.announcements],
        }
