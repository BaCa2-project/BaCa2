from django.urls import path

from . import views

urlpatterns = [
    path("<str:course>/<int:submit_id>", views.handle_broker, name='brokerApi')
]
