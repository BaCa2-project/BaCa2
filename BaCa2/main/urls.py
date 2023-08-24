from django.urls import path
from .views import (DashboardView,
                    CoursesView,
                    JsonView,

                    TestView,
                    jsontest,
                    change_theme)

app_name = 'main'

urlpatterns = [
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('courses', CoursesView.as_view(), name='courses'),
    path('json/<str:model_name>', JsonView.as_view(), name='json'),

    path('test', TestView.as_view(), name='test'),
    path('jsontest', jsontest, name='jsontest'),
    path('change_theme', change_theme, name='change-theme'),
]
