from django.urls import path
from .views import TestView, DashboardView, jsontest, change_theme

app_name = 'main'

urlpatterns = [
    path('test', TestView.as_view(), name='test'),
    path('jsontest', jsontest, name='jsontest'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('change_theme', change_theme, name='change-theme'),
]
