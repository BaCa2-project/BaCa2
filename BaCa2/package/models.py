from django.db import models
from main.models import User
from .validators import isStr
from BaCa2.settings import BASE_DIR, PACKAGES
from course.models import Task
from pathlib import Path
from BaCa2.settings import PACKAGES
from package_manage import Package

from django.utils import timezone
from django.db import transaction


class PackageSource(models.Model):
    MAIN_SOURCE = BASE_DIR / 'packages'

    name = models.CharField(max_length=511, validators=[isStr])

    def __str__(self):
        return f"Package: {self.name}"

    @property
    def path(self):
        return self.MAIN_SOURCE / self.name


class PackageInstanceUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package_instance = models.ForeignKey('PackageInstance', on_delete=models.CASCADE)


class PackageInstance(models.Model):
    package_source = models.ForeignKey(PackageSource, on_delete=models.CASCADE)
    commit = models.CharField(max_length=2047)

    @classmethod
    def exists(cls, pkg_id: int):
        """
        If the package with the given ID exists, return True, otherwise return False

        :param pkg_id: The id of the package to check for
        :type pkg_id: int
        :return: A boolean value.
        """
        return cls.objects.filter(pk=pkg_id).exists()

    def __str__(self):
        pass    #TODO

    @property
    def key(self):
        return f"{self.package_source.name}.{self.commit}"

    @property
    def package(self) -> Package:
        package_id = self.key
        return PACKAGES.get(package_id)

    @property
    def path(self):
        return self.package_source.path / self.commit

    def create_from_me(self):
        # PackageInstance.objects.create(path)
        new_path = self.package_source.path
        new_commit = timezone.now().timestamp()

        new_package = self.package.copy(new_path, new_commit)  # PackageManager TODO: COPY
        new_package.check_package()

        commit_msg = f"{self.package_source.name}.{new_commit}"
        PACKAGES[commit_msg] = new_package

        new_instance = PackageInstance.objects.create(
            package_source=self.package_source,
            commit=new_commit
        )

        return new_instance

    """
           function to delete package commit

           :return: A boolean value.
    """

    def delete_instance(self):
        if Task.check_instance(self):
            raise

        with transaction.atomic():
            self.package.delete()
            PACKAGES.pop(self.key)
            self.delete()

        # deleting instance in source directory
        # # self delete instance

    def share(self, user: User):
        new_instance = self.create_from_me()
        PackageInstanceUser.objects.create(user=user, package_instance=new_instance)
