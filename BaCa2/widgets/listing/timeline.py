from widgets.base import Widget


class Event(Widget):
    DEFAULT_ICON = 'check-lg'

    def __init__(self, *,
                 name: str,
                 title: str,
                 content: str,
                 icon: str = '',
                 date: str = '') -> None:
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
    def __init__(self, *,
                 name: str,
                 events: list[Event],
                 default_icon: str = '',
                 scroll_to: str = '') -> None:
        super().__init__(name)

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
        if not event.icon:
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
