from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from course.manager import resend_pending_submits


class CourseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'course'
    verbose_name = _('Course')

    def ready(self):
        """
        It migrates all the tables in the database when app is loaded.
        """

        settings.DB_MANAGER.migrate_all()
        resend_pending_submits()
