from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CourseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'course'
    verbose_name = _('Course')

    def ready(self):
        """
        It migrates all the tables in the database when app is loaded.
        """
        from BaCa2.db.creator import migrateAll
        migrateAll()
