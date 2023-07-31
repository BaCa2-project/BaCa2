from django.views.generic.base import TemplateView
from django.http import JsonResponse
from .models import Course
from widgets.querying import get_queryset
from widgets.listing import Table


class TestView(TemplateView):
    template_name = 'test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        table = Table(model_cls=Course,
                      refresh=True,
                      refresh_interval=30000,
                      paging=True,
                      page_length=4,
                      length_change=True,)

        context['table'] = table.get_context()
        return context


def jsontest(request):
    return JsonResponse({'data': [course.get_data() for course in get_queryset(Course)]})
