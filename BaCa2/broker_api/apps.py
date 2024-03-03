from django.apps import AppConfig
from django.core.management import call_command


class BrokerApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'broker_api'

    def ready(self):
        call_command('markExpired')
        call_command('resendToBroker')
