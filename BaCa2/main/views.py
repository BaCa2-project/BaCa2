from django.views.generic.base import TemplateView, RedirectView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import JsonResponse
from django.urls import reverse_lazy

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


class BaCa2LogoutView(RedirectView):
    url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class LoggedInView(LoginRequiredMixin, TemplateView):
    template_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['display_navbar'] = True
        context['navbar'] = self.get_navbar_context()

        context['data_bs_theme'] = self.request.user.user_settings.theme
        return context

    def get_navbar_context(self):
        context = {'links': [
            {'name': 'Dashboard', 'url': reverse_lazy('main:dashboard')},
            {'name': 'Kursy', 'url': reverse_lazy('main:courses')},
            {'name': 'Zadania', 'url': '#'},  # TODO
        ]}

        if self.request.user.is_staff:
            context['links'].append({'name': 'Paczki', 'url': '#'})  # TODO

        return context


class DashboardView(LoggedInView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['display_navbar'] = True
        return context


class CoursesView(LoggedInView):
    template_name = 'courses.html'


class JsonView(LoginRequiredMixin, View):
    @staticmethod
    def get(request, *args, **kwargs):
        if kwargs['model_name'] == 'course':
            return JsonResponse(
                {'data': [course.get_data() for course in Course.objects.filter(
                    usercourse__user=request.user
                )]}
            )


class TestView(LoggedInView):
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


def change_theme(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            theme = request.POST.get('theme')
            request.user.user_settings.theme = theme
            request.user.user_settings.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})
