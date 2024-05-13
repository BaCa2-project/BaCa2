from typing import List

from widgets.base import Widget


class SideNavTab(Widget):
    DEFAULT_ICON = 'hexagon-half'

    def __init__(self, *,
                 name: str,
                 title: str,
                 icon: str | None = None,
                 hint_text: str | None = None,
                 sub_tabs: List['SideNavTab'] = None) -> None:
        super().__init__(name=name, widget_class='sidenav-tab')
        self.title = title
        self.icon = icon or self.DEFAULT_ICON
        self.hint_text = hint_text
        self.sub_tabs = sub_tabs or []

        names = self.get_names()
        self.name_set = set()

        for name in names:
            if name in self.name_set:
                raise ValueError(f'Duplicate tab name: {name}')
            self.name_set.add(name)

    def get_names(self) -> List[str]:
        out = [self.name]

        for sub_tab in self.sub_tabs:
            out.extend(sub_tab.get_names())

        return out

    def add_sub_tab(self, sub_tab: 'SideNavTab', index: int = -1) -> None:
        names = sub_tab.get_names()

        for name in names:
            if name in self.name_set:
                raise ValueError(f'Duplicate tab name: {name}')

        self.name_set.update(names)

        if index == -1:
            self.sub_tabs.append(sub_tab)
        else:
            self.sub_tabs.insert(index, sub_tab)

    def get_tab(self, name: str) -> 'SideNavTab':
        if name not in self.name_set:
            raise ValueError(f'Tab not found: {name}')

        if name == self.name:
            return self

        for sub_tab in self.sub_tabs:
            if name in sub_tab.name_set:
                return sub_tab.get_tab(name)

    def get_context(self) -> dict:
        return super().get_context() | {
            'title': self.title,
            'hint_text': self.hint_text,
            'icon': self.icon,
            'sub_tabs': [sub_tab.get_context() for sub_tab in self.sub_tabs]
        }


class SideNav(Widget):
    def __init__(self, *,
                 tabs: List[SideNavTab] = None,
                 collapsed: bool = False,
                 sticky: bool = True,
                 toggle_button: bool = False) -> None:
        super().__init__(name='sidenav', widget_class='sidenav')
        self.tabs = tabs or []
        self.name_set = set()
        self.sticky = sticky
        self.collapsed = collapsed
        self.toggle_button = toggle_button

        for tab in self.tabs:
            names = tab.get_names()

            for name in names:
                if name in self.name_set:
                    raise ValueError(f'Duplicate tab name: {name}')
                self.name_set.add(name)

    @property
    def collapsed(self) -> bool:
        return 'collapsed' in self.widget_class

    @collapsed.setter
    def collapsed(self, value: bool) -> None:
        if value:
            self.add_class('collapsed')
        else:
            self.remove_class('collapsed')

    @property
    def sticky(self) -> bool:
        return 'sticky' in self.widget_class

    @sticky.setter
    def sticky(self, value: bool) -> None:
        if value:
            self.add_class('sticky')
        else:
            self.remove_class('sticky')

    def get_tab(self, name: str) -> SideNavTab:
        for tab in self.tabs:
            if name in tab.name_set:
                return tab.get_tab(name)
        raise ValueError(f'Tab not found: {name}')

    def add_tab(self, tab: SideNavTab, index: int = -1, under: str | None = None) -> None:
        names = tab.get_names()

        for name in names:
            if name in self.name_set:
                raise ValueError(f'Duplicate tab name: {name}')

        if under:
            self.get_tab(under).add_sub_tab(tab, index)
        else:
            if index == -1:
                self.tabs.append(tab)
            else:
                self.tabs.insert(index, tab)

        self.name_set.update(names)

    def get_context(self) -> dict:
        return super().get_context() | {
            'tabs': [tab.get_context() for tab in self.tabs],
            'collapsed': self.collapsed,
            'sticky': self.sticky,
            'toggle_button': self.toggle_button
        }
