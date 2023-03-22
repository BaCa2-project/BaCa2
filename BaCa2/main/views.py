from django.views.generic.base import TemplateView
from .models import Course
from widgets.querying import get_queryset
from widgets.listing import Table


class TestView(TemplateView):
    template_name = 'test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['courses'] = get_queryset(
            Course
        )

        context['names'] = [context['courses'][_].name for _ in range(len(context['courses']))]
        context['short_names'] = [context['courses'][_].short_name for _ in range(len(context['courses']))]
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
            queryset,
            ['name', 'short_name', 'db_name'],
            None,
            {'name': 'Course Name', 'short_name': 'Short Name'}
        )

        context['table'] = table.get_context()
        return context
