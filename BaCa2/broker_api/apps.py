from django.apps import AppConfig
from django.conf import settings


class BrokerApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'broker_api'

    def ready(self):
        # Add broker scheduled jobs
        if settings.BROKER_RETRY_POLICY.auto_start:
            from broker_api.scheduler import JOBS
            for job in JOBS:
                settings.SCHEDULER.add_job(**job)
