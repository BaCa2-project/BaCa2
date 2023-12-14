from django.urls import path

from . import views

urlpatterns = [
    path("result", views.handle_broker_result, name='brokerApiResult'),
    path("error", views.handle_broker_error, name="brokerApiError")
]
