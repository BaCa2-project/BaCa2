from django.apps import AppConfig
from django.conf import settings


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        if settings.AUTO_REFRESH_RANKINGS:
            from main.scheduler import REFRESH_RANKINGS_JOB
            settings.SCHEDULER.add_job(**REFRESH_RANKINGS_JOB)
