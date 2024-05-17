from typing import Any, Dict, List

from django.http.request import HttpRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from util.models_registry import ModelsRegistry
# from core.choices import BasicModelAction
# from package.models import PackageInstance
from widgets.base import Widget


class NavBar(Widget):
    """
    Navbar widget containing links to the most important pages. Visible links depend on user's
    permissions.
    """

    def __init__(self, request: HttpRequest) -> None:
        """
        :param request: Request object used to determine user's permissions and to generate links.
        :type request: HttpRequest
        """
        super().__init__(name='navbar', request=request)

        self.links = [
            {'name': _('Dashboard'), 'url': reverse_lazy('main:dashboard')},
            {'name': _('Timeline'), 'url': reverse_lazy('main:dev-timeline')},
            {'name': _('Courses'), 'url': reverse_lazy('main:courses')},
            # {'name': _('Tasks'), 'url': '#'}
        ]

        # if request.user.has_basic_model_permissions(model=PackageInstance,
        #                                             permissions=BasicModelAction.VIEW):
        #     self.links.append({'name': _('Packages'), 'url': '#'})

        if request.user.is_superuser:
            self.links.append({'name': _('Admin'), 'url': reverse_lazy('main:admin')})

        course_id = getattr(request, 'course_id', None)

        if course_id:
            course = ModelsRegistry.get_course(course_id)
            self.links.append('|')
            self.links.append(
                {'name': course.name,
                 'url': reverse_lazy('course:course-view', kwargs={'course_id': course_id})}
            )

    def get_context(self) -> Dict[str, Any]:
        return {'links': self.links}


class SideNav(Widget):
    """
    Side navigation widget containing a custom set of tabs. Tabs are all part of the same page and
    unlike in the navbar do not represent links to other urls.
    """

    def __init__(self,
                 request: HttpRequest,
                 tabs: List[str],
                 sub_tabs: Dict[str, List[str]] = None,
                 collapsed: bool = False,
                 toggle_button: bool = False,
                 sticky: bool = True) -> None:
        """
        :param request: HTTP request object received by the view this side nav panel is rendered in.
        :type request: HttpRequest
        :param tabs: List of tab names.
        :type tabs: List[str]
        :param sub_tabs: Dictionary of sub-tabs. Each key is the name of the tab and the value is a
            list of sub-tab names.
        :type sub_tabs: Dict[str, List[str]]
        :param collapsed: Whether the side navigation sub-tabs should be collapsed by default and
            expand only on hover/use (or when the toggle button is clicked).
        :type collapsed: bool
        :param toggle_button: Whether the toggle button should be displayed. Toggle button is used
            to expand/collapse the side navigation sub-tabs.
        :type toggle_button: bool
        :param sticky: Whether the side navigation should be sticky and always visible.
        :type sticky: bool
        """
        super().__init__(name='sidenav', request=request)
        sub_tabs = sub_tabs or {}

        self.toggle_button = {'on': toggle_button,
                              'state': collapsed,
                              'text_collapsed': _('Expand'),
                              'text_expanded': _('Collapse')}

        self.tabs = [
            {
                'name': tab_name,
                'data_id': SideNav.normalize_tab_name(tab_name) + '-tab',
                'sub_tabs': [{'name': sub_tab_name,
                              'data_id': SideNav.normalize_tab_name(sub_tab_name) + '-tab'}
                             for sub_tab_name in sub_tabs.get(tab_name, [])]
            }
            for tab_name in tabs
        ]

        if sticky:
            self.add_class('sticky-side-nav')
        if collapsed:
            self.add_class('collapsed')
        else:
            self.add_class('expanded')

    @staticmethod
    def normalize_tab_name(tab_name: str) -> str:
        """
        Normalizes tab name by replacing spaces with dashes and converting to lowercase.

        :param tab_name: Tab name to normalize.
        :type tab_name: str

        :return: Normalized tab name.
        :rtype: str
        """
        return tab_name.replace(' ', '-').lower()

    def get_context(self) -> Dict[str, Any]:
        return super().get_context() | {'tabs': self.tabs, 'toggle_button': self.toggle_button}

    def add_tab(self, tab_name: str, sub_tabs: List[str] = None) -> None:
        """
        Adds a new tab to the side navigation.

        :param tab_name: Name of the tab to add.
        :type tab_name: str
        :param sub_tabs: List of sub-tab names.
        :type sub_tabs: List[str]
        """
        new_tab = {
            'name': tab_name,
            'data_id': SideNav.normalize_tab_name(tab_name) + '-tab',
            'sub_tabs': []
        }
        if sub_tabs:
            new_tab['sub_tabs'] = [{'name': sub_tab_name,
                                    'data_id': SideNav.normalize_tab_name(sub_tab_name) + '-tab'}
                                   for sub_tab_name in sub_tabs]
        self.tabs.append(new_tab)


class SidenavTab(Widget):
    DEFAULT_ICON = 'hexagon-half'

    def __init__(self, *,
                 name: str,
                 title: str,
                 icon: str | None = None,
                 hint_text: str | None = None,
                 sub_tabs: List['SidenavTab'] = None,
                 parent_tab: bool = False) -> None:
        super().__init__(name=name, widget_class='sidenav-tab')
        self.title = title
        self.icon = icon or self.DEFAULT_ICON
        self.hint_text = hint_text
        self.sub_tabs = sub_tabs or []
        self.parent_tab = parent_tab

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

    def add_sub_tab(self, sub_tab: 'SidenavTab', index: int = -1) -> None:
        names = sub_tab.get_names()

        for name in names:
            if name in self.name_set:
                raise ValueError(f'Duplicate tab name: {name}')

        self.name_set.update(names)

        if index == -1:
            self.sub_tabs.append(sub_tab)
        else:
            self.sub_tabs.insert(index, sub_tab)

    def get_tab(self, name: str) -> 'SidenavTab':
        if name not in self.name_set:
            raise ValueError(f'Tab not found: {name}')

        if name == self.name:
            return self

        for sub_tab in self.sub_tabs:
            if name in sub_tab.name_set:
                return sub_tab.get_tab(name)

    def to_remove(self) -> bool:
        return self.parent_tab and not self.sub_tabs

    def get_context(self) -> dict:
        if len(self.sub_tabs) == 1:
            self.name = self.sub_tabs[0].name
            self.sub_tabs = []
        if self.sub_tabs:
            self.add_class('has-sub-tabs')

        return super().get_context() | {
            'title': self.title,
            'hint_text': self.hint_text,
            'icon': self.icon,
            'sub_tabs': [sub_tab.get_context() for sub_tab in self.sub_tabs]
        }


class Sidenav(Widget):
    def __init__(self, *,
                 tabs: List[SidenavTab] = None,
                 sticky: bool = True,
                 toggle_button: bool = False) -> None:
        super().__init__(name='sidenav', widget_class='sidenav')
        self.tabs = tabs or []
        self.name_set = set()
        self.sticky = sticky
        self.toggle_button = toggle_button

        for tab in self.tabs:
            names = tab.get_names()

            for name in names:
                if name in self.name_set:
                    raise ValueError(f'Duplicate tab name: {name}')
                self.name_set.add(name)

    @property
    def sticky(self) -> bool:
        return 'sticky' in self.widget_class

    @sticky.setter
    def sticky(self, value: bool) -> None:
        if value:
            self.add_class('sticky')
        else:
            self.remove_class('sticky')

    def get_tab(self, name: str) -> SidenavTab:
        for tab in self.tabs:
            if name in tab.name_set:
                return tab.get_tab(name)
        raise ValueError(f'Tab not found: {name}')

    def add_tab(self, tab: SidenavTab, index: int = -1, under: str | None = None) -> None:
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
            'tabs': [tab.get_context() for tab in self.tabs if not tab.to_remove()],
            'sticky': self.sticky,
            'toggle_button': self.toggle_button
        }
