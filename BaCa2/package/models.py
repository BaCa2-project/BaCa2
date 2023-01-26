from django.db import models
from main.models import User
from .validators import isStr
from BaCa2.settings import BASE_DIR
# from course.models import Task
from pathlib import Path
from BaCa2.settings import PACKAGES
from .package_manage import Package

from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError


class PackageSource(models.Model):
    """
    PackageSource is a source for packages instances
    """
    #: path to the main source
    MAIN_SOURCE = BASE_DIR / 'packages'
    #: name of the package
    name = models.CharField(max_length=511, validators=[isStr])

    def __str__(self):
        return f"Package {self.pk}: {self.name}"

    @property
    def path(self) -> Path:
        """
        It returns the path to the main source directory for package instance

        :return: The path to the file.
        """
        return self.MAIN_SOURCE / self.name


class PackageInstanceUser(models.Model):
    """
    A PackageInstanceUser is a user who is associated with a package instance.
    """
    #: User associated with the package instance
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #: package instance associated with the user
    package_instance = models.ForeignKey('PackageInstance', on_delete=models.CASCADE)


class PackageInstance(models.Model):
    """
    A PackageInstance is a unique version of a PackageSource.
    """
    #: foreign key to the PackageSource class :py:class:`PackageSource`
    # This means that each PackageInstance is associated with a single PackageSource
    package_source = models.ForeignKey(PackageSource, on_delete=models.CASCADE)
    #: unique identifier for every package instance
    commit = models.CharField(max_length=2047)

    @classmethod
    def exists(cls, pkg_id: int) -> bool:
        """
        If the package with the given ID exists, return True, otherwise return False

        :param pkg_id: The id of the package to check for
        :type pkg_id: int

        :return: A boolean value.
        """
        return cls.objects.filter(pk=pkg_id).exists()

    def __str__(self):
        """
        The __str__ function is a special function that is called when you print an object

        :return: The key of the package instance.
        """
        return f"Package Instance: {self.key}"

    @property
    def key(self) -> str:
        """
        It returns a string that is the name of the package source and the commit

        :return: The name of the package source and the commit.
        """
        return f"{self.package_source.name}.{self.commit}"

    @property
    def package(self) -> Package:
        """
        It returns the package id of the key.

        :return: The package object.
        """
        package_id = self.key
        return PACKAGES.get(package_id)

    @property
    def path(self) -> Path:
        """
        It returns the path to the package's source code

        :return: The path to the package source and the commit.
        """
        return self.package_source.path / self.commit

    def create_from_me(self) -> 'PackageInstance':
        """
        Create a new package instance from the current package instance

        :return: A new PackageInstance object.
        """
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

    def delete_instance(self):
        """
        If the task is not in the database, raise an exception.
        Otherwise, delete the task and its package from the database
        """
        from course.models import Task
        if Task.check_instance(self):
            raise ValidationError('Package is used and you cannot delete it')

        with transaction.atomic():
            # deleting instance in source directory
            self.package.delete()
            PACKAGES.pop(self.key)
            # self delete instance
            self.delete()

    def share(self, user: User):
        """
        It creates a new instance of a package, and then creates a new PackageInstanceUser object that links
        the new package instance to the user

        :param user: The user to share the package with
        :type user: User
        """
        new_instance = self.create_from_me()
        PackageInstanceUser.objects.create(user=user, package_instance=new_instance)
