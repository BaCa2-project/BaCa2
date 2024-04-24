from typing import List

from widgets.base import Widget


class Event(Widget):
    """
    A single event in a timeline. Represented by a point in the timeline accompanied by a card with
    given title, content and date.
    """

    #: Default icon to be used to mark event on the timeline if no icon is provided
    DEFAULT_ICON = 'check-lg'

    def __init__(self, *,
                 name: str,
                 title: str,
                 content: str,
                 icon: str = '',
                 date: str = '') -> None:
        """
        :param name: Unique name of the event
        :type name: str
        :param title: Title of the event
        :type title: str
        :param content: Description of the event
        :type content: str
        :param icon: Icon to be displayed in the timeline. If not provided, default icon is used
            instead (see `Event.DEFAULT_ICON`)
        :type icon: str
        :param date: Date of the event. If provided will be displayed in the event card next to the
            title
        :type date: str
        """
        super().__init__(name)
        self.title = title
        self.content = content
        self.date = date
        self.icon = icon

    def get_context(self) -> dict:
        return super().get_context() | {
            'title': self.title,
            'content': self.content,
            'date': self.date,
            'icon': self.icon or self.DEFAULT_ICON,
        }


class Timeline(Widget):
    """
    A timeline widget. Consists of multiple events that are displayed along a vertical line. Each
    event is represented by a point in the timeline and a card with title, content and date.
    """

    def __init__(self, *,
                 name: str,
                 events: List[Event],
                 default_icon: str = '',
                 scroll_to: str = '') -> None:
        """
        :param name: Unique name of the timeline
        :type name: str
        :param events: List of events to be displayed in the timeline
        :type events: List[Event]
        :param default_icon: Default icon to be used to mark events on the timeline if no icon is
            provided for a given event (optional)
        :type default_icon: str
        :param scroll_to: Name of the event to scroll to when the page containing the timeline is
            loaded
        :type scroll_to: str
        :raises ValueError: If `scroll_to` is provided and no event with given name is found
        """
        super().__init__(name)

        if default_icon:
            for event in events:
                if not event.icon:
                    event.icon = default_icon

        if scroll_to and scroll_to not in (event.name for event in events):
            raise ValueError(f'Event with name "{scroll_to}" not found')

        self.events = events
        self.default_icon = default_icon
        self.scroll_to = scroll_to

    def get_context(self) -> dict:
        return super().get_context() | {
            'events': [event.get_context() for event in self.events],
            'scroll_to': self.scroll_to,
        }

    def add_event(self, event: Event) -> None:
        """
        Add a new event to the timeline. If no icon is provided for the event, default icon is used
        (if set).

        :param event: Event to be added to the timeline
        :type event: Event
        """
        if self.default_icon and not event.icon:
            event.icon = self.default_icon

        self.events.append(event)


class ReleaseEvent(Event):
    UNRELEASED_ICON = 'tag'
    RELEASED_ICON = 'tag-fill'

    def __init__(self, *,
                 tag: str,
                 date: str,
                 description: str,
                 released: bool) -> None:
        super().__init__(name=tag,
                         title=tag,
                         content=description,
                         date=date,
                         icon=self.RELEASED_ICON if released else self.UNRELEASED_ICON)
        self.add_class('released' if released else 'unreleased')
