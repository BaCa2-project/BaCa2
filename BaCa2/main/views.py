from django.views.generic.base import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import JsonResponse

from .models import Course
from widgets.querying import get_queryset
from widgets.listing import TableWidget
from widgets.forms import FormWidget


class BaCa2LoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_widget'] = FormWidget(button_text='Zaloguj').get_context()
        context['display_navbar'] = False
        context['data_bs_theme'] = 'dark'
        return context


class LoggedInView(LoginRequiredMixin, TemplateView):
    template_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['display_navbar'] = True
        context['data_bs_theme'] = self.request.user.user_settings.theme
        return context


class DashboardView(LoggedInView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['display_navbar'] = True
        return context


class TestView(LoginRequiredMixin, TemplateView):
    template_name = 'test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        table = TableWidget(model_cls=Course,
                            refresh=True,
                            refresh_interval=30000,
                            paging=True,
                            page_length=4,
                            length_change=True,)

        context['table'] = table.get_context()
        return context


def jsontest(request):
    return JsonResponse({'data': [course.get_data() for course in get_queryset(Course)]})
