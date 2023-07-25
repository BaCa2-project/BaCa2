from django.views.generic.base import TemplateView
from .models import Course, Group
from widgets.querying import get_queryset
from widgets.listing import Table


class TestView(TemplateView):
    template_name = 'test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = get_queryset(
            Course
        )
        table = Table(
            queryset=queryset,
            cols=['name', 'short_name', 'db_name'],
            header={'name': 'Course Name', 'short_name': 'Short Name'},
            sortable=True,
            searchable=True
        )

        queryset2 = get_queryset(
            Group
        )
        table2 = Table(
            queryset=queryset2,
            cols=['name'],
            header={'name': 'Group Name'},
            sortable=True,
        )

        context['table1'] = table.get_context()
        context['table2'] = table2.get_context()
        return context


class TestViewList(TemplateView):
    template_name = 'testlist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = get_queryset(
            Course,
            {'id': [1, 2, 3]}
        )
        table = Table(
            queryset=queryset,
            cols=['name', 'short_name', 'db_name'],
            header={'name': 'Course Name', 'short_name': 'Short Name'}
        )

        context['table'] = table.get_context()
        return context
