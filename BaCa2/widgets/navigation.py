from typing import (Any, Dict, List)

from django.http.request import HttpRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

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
        super().__init__('navbar')
        self.links = [
            {'name': 'Dashboard', 'url': reverse_lazy('main:dashboard')},
            {'name': 'Kursy', 'url': reverse_lazy('main:courses')},
            {'name': 'Zadania', 'url': '#'},  # TODO: add url
        ]

        if request.user.is_staff:
            self.links.append({'name': _('Packages'), 'url': '#'})  # TODO: add url

        if request.user.is_superuser:
            self.links.append({'name': _('Admin'), 'url': reverse_lazy('main:admin')})

    def get_context(self) -> Dict[str, Any]:
        return {'links': self.links}


class SideNav(Widget):
    """
    Side navigation widget containing a custom set of tabs. Tabs are all part of the same page and
    unlike in the navbar do not represent links to other urls.
    """

    def __init__(self, *args: str, **kwargs: List[str]) -> None:
        """
        :param args: Names of the tabs.
        :type args: str
        :param kwargs: Optional sub-tabs for each tab. If a tab has sub-tabs the kwargs should
        contain

        """
        super().__init__('sidenav')
        self.tabs = [
            {
                'name': tab_name,
                'data_id': tab_name + '-tab',
                'sub_tabs': [{'name': sub_tab_name, 'data_id': sub_tab_name + '-tab'}
                             for sub_tab_name in kwargs.get(tab_name, [])]
            }
            for tab_name in args

            # TODO: add handling for tab names with spaces
        ]

    def get_context(self) -> Dict[str, Any]:
        return {'tabs': self.tabs}
