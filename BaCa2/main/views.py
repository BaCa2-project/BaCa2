from django.views.generic.base import TemplateView, RedirectView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import JsonResponse
from django.urls import reverse_lazy

from .models import Course
from widgets.listing import TableWidget
from widgets.forms import FormWidget, NewCourseForm, NewCourseFormWidget


class BaCa2LoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_widget'] = FormWidget(form=context['form'],
                                            button_text='Zaloguj',
                                            display_field_errors=False).get_context()
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

        if self.request.user.is_superuser:
            context['links'].append({'name': 'Admin', 'url': reverse_lazy('main:admin')})

        return context


class AdminView(LoggedInView, UserPassesTestMixin):
    template_name = 'admin.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'new_course_form_widget' not in context.keys():
            context['new_course_form_widget'] = NewCourseFormWidget().get_context()
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('form_name', None) == 'new_course_form':
            form = NewCourseForm(data=request.POST)

            if form.is_valid():
                Course.objects.create_course(
                    name=form.cleaned_data['name'],
                    short_name=form.cleaned_data.get('short_name', None),
                )
                return JsonResponse({'status': 'ok'})
            else:
                kwargs['new_course_form_widget'] = NewCourseFormWidget(form=form).get_context()
                return self.get(request, *args, **kwargs)
        else:
            return JsonResponse(
                {'status': 'error, unknown form name',
                 'form_name': request.POST.get('form_name', None)}
            )


class DashboardView(LoggedInView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['display_navbar'] = True
        return context


class CoursesView(LoggedInView):
    template_name = 'courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        table = TableWidget(model_cls=Course,
                            refresh=False,
                            paging=False)

        context['table'] = table.get_context()
        return context


class JsonView(LoginRequiredMixin, View):
    @staticmethod
    def get(request, *args, **kwargs):
        if kwargs['model_name'] == 'course':
            return JsonResponse(
                {'data': [course.get_data() for course in Course.objects.filter(
                    usercourse__user=request.user
                )]}
            )
        return JsonResponse({'status': 'error'})


def change_theme(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            theme = request.POST.get('theme')
            request.user.user_settings.theme = theme
            request.user.user_settings.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})
