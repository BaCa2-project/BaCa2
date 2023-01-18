from django.db import models
from main.models import User
from .validators import isStr
from BaCa2.settings import BASE_DIR, PACKAGES
from course.models import Task
from pathlib import Path
from BaCa2.settings import PACKAGES
from package_manage import Package


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

    def get_commit(self):
        return f"{self.package_source.name}.{self.commit}"

    def get_package_manager(self):
        return PACKAGES[self.get_commit()]

    @property
    def package(self):
        package_id = self.get_commit()
        return PACKAGES.get(package_id)

    @property
    def path(self):
        return self.package_source.path / self.commit

    def create_from_me(self, new_path, new_commit):
        # PackageInstance.objects.create(path)
        new_package = self.package.copy(new_path, new_commit)
        PACKAGES[new_package.get_commit()] = Package(new_package.path())
        return new_package


    """
           function to delete package commit

           :return: A boolean value.
    """
    def delete_instance(self):
        if Task.check_instance(self):
            raise
        # deleting instance in source directory
        file = Path(self.package_source.path / self.commit).resolve()
        file.unlink()
        # self delete instance
        self.delete()

    def share(self, user: User):
        # new_instance = self.create_from_me()
        new_instance = "x"
        PackageInstanceUser.objects.create(user=user, package_instance=new_instance)
