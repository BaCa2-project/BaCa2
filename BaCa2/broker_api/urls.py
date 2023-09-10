from django.urls import path

from . import views

urlpatterns = [
    path("result/<str:course>/<int:submit_id>", views.handle_broker_result, name='brokerApiResult'),
    path("status/<str:course>/<int:submit_id>", views.handle_broker_status, name='brokerApiStatus')
]
