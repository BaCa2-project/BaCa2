from typing import (Any, Dict, List)

from django.http.request import HttpRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from widgets.base import Widget
from package.models import PackageInstance
from BaCa2.choices import BasicPermissionType


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
            {'name': _('Courses'), 'url': reverse_lazy('main:courses')},
            {'name': _('Tasks'), 'url': '#'}
        ]

        if request.user.has_basic_model_permissions(model=PackageInstance,
                                                    permissions=BasicPermissionType.VIEW):
            self.links.append({'name': _('Packages'), 'url': '#'})

        if request.user.is_superuser:
            self.links.append({'name': _('Admin'), 'url': reverse_lazy('main:admin')})

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
                 toggle_button: bool = False) -> None:
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
        """
        super().__init__(name='sidenav', request=request)
        sub_tabs = sub_tabs or {}
        self.collapsed = collapsed
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
        return {'tabs': self.tabs,
                'collapsed': self.collapsed,
                'toggle_button': self.toggle_button}
