from django.apps import AppConfig


class BrokerApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'broker_api'

    def ready(self):
        super().ready()
        # call_command('markExpired')
        # call_command('resendToBroker')
