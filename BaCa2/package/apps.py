from django.apps import AppConfig


class PackageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'package'

    def ready(self):
        pass
        # from django.db.utils import ProgrammingError

        # try:
        #     from .models import PackageInstance
        #     for instance in PackageInstance.objects.all():
        #         PACKAGES[instance.key] = Package(instance.package_source.path, instance.commit)
        # except ProgrammingError:
        #     pass
