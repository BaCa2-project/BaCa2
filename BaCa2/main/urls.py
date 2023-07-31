from django.urls import path
from .views import TestView, jsontest

app_name = 'main'

urlpatterns = [
    path('test', TestView.as_view(), name='test'),
    path('jsontest', jsontest, name='jsontest')
]
