from django.apps import AppConfig

from baca2PackageManager import Package
from core.settings import PACKAGES


class PackageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'package'

    def ready(self):
        from django.db.utils import ProgrammingError
        try:
            from .models import PackageInstance
            for instance in PackageInstance.objects.all():
                PACKAGES[instance.key] = Package(instance.package_source.path, instance.commit)
        except ProgrammingError:
            pass
