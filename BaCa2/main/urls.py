from django.urls import path
from .views import (DashboardView,
                    CoursesView,
                    JsonView,
                    AdminView,

                    change_theme)

app_name = 'main'

urlpatterns = [
    path('admin', AdminView.as_view(), name='admin'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('courses', CoursesView.as_view(), name='courses'),
    path('json/<str:model_name>', JsonView.as_view(), name='json'),

    path('change_theme', change_theme, name='change-theme'),
]
