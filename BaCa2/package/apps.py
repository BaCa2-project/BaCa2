from django.apps import AppConfig
from BaCa2.settings import PACKAGES
from package_manage import Package


class PackageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'package'

    def ready(self):
        from django.db.utils import ProgrammingError
        try:
            from .models import PackageInstance
            for instance in PackageInstance.objects.all():
                PACKAGES[instance.get_commit(self)] = Package(instance.path(self))
        except ProgrammingError:
            pass
