from django.urls import path
from django.views.generic import TemplateView
from .views import TestView, TestViewList

app_name = 'main'

urlpatterns = [
    path('test', TestView.as_view(), name='test'),
    path('testlist', TestViewList.as_view(), name='testlist')
]