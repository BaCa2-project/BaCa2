from __future__ import annotations

from typing import Self

from django.db import models
from main.models import User
from baca2PackageManager.validators import isStr
from BaCa2.settings import BASE_DIR
# from course.models import Task
from pathlib import Path
from BaCa2.settings import PACKAGES, PACKAGES_DIR
from baca2PackageManager import Package

from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from util.models_registry import ModelsRegistry


class PackageSourceManager(models.Manager):
    """
    PackageSourceManager is a manager for the PackageSource class
    """

    def get_unique_name(self, name: str) -> str:
        """
        It returns a unique name for the package source

        :param name: The name of the package source
        :type name: str

        :return: The unique name of the package source.
        """
        if not self.model.exists(name):
            return name

        i = 1
        while self.model.exists(f"{name}{i}"):
            i += 1
        return f"{name}{i}"

    @transaction.atomic
    def create_package_source(self, name: str) -> PackageSource:
        """
        Create a new package source from the given name

        :param name: The name of the package source
        :type name: str

        :return: A new PackageSource object.
        """
        package_source = self.model(name=name)
        package_source.save()
        return package_source

    def create_package_source_from_zip(self, zip_file: Path) -> PackageSource:
        """
        Create a new package source from the given zip file

        :param zip_file: The path to the zip file
        :type zip_file: Path

        :return: A new PackageSource object.
        """
        raise NotImplementedError("create_package_source_from_zip is not implemented yet")

    @transaction.atomic
    def delete_package_source(self, package_source: PackageSource):
        """
        If the package source is not in the database, raise an exception.
        Otherwise, delete the package source and its package from the database

        :param package_source: The package source to delete
        :type package_source: PackageSource
        """
        for instance in package_source.instances:
            instance.objects.delete_package_instance()
        package_source.delete()


class PackageSource(models.Model):
    """
    PackageSource is a source for packages instances
    """
    #: path to the main source
    MAIN_SOURCE = PACKAGES_DIR  # TODO
    #: name of the package
    name = models.CharField(max_length=511, validators=[isStr])

    #: manager for the PackageSource class
    objects = PackageSourceManager()

    def __str__(self):
        return f"Package {self.pk}: {self.name}"

    @property
    def path(self) -> Path:
        """
        It returns the path to the main source directory for package instance

        :return: The path to the file.
        """
        return self.MAIN_SOURCE / self.name

    @property
    def instances(self):
        """
        It returns the instances of the package source

        :return: The instances of the package source.
        """
        return PackageInstance.objects.filter(package_source=self)


class PackageInstanceUserManager(models.Manager):
    """
    PackageInstanceUserManager is a manager for the PackageInstanceUser class
    """

    @transaction.atomic
    def create_package_instance_user(
            self,
            user: int | str | User,
            package_instance: int | str | PackageInstance
    ) -> PackageInstanceUser:
        """
        Create a new package instance user from the given user and package instance

        :param user: The user
        :type user: User
        :param package_instance: The package instance
        :type package_instance: PackageInstance

        :return: A new PackageInstanceUser object.
        """
        user = ModelsRegistry.get_user(user)
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        package_instance_user = self.model(user=user, package_instance=package_instance)
        package_instance_user.save()
        return package_instance_user

    @transaction.atomic
    def delete_package_instance_user(self, package_instance_user: PackageInstanceUser):
        """
        If the package instance user is not in the database, raise an exception.
        Otherwise, delete the package instance user from the database

        :param package_instance_user: The package instance user to delete
        :type package_instance_user: PackageInstanceUser
        """
        package_instance_user.delete()

    def check_user(self,
                   user: int | str | User,
                   package_instance: int | PackageInstance) -> bool:
        """
        Checks if user is associated with package instance.

        :param user: The user to be checked
        :type user: int | str | User
        :param package_instance: The package instance to be checked
        :type package_instance: int | PackageInstance

        :return: True if user is associated with package instance, False otherwise.
        :rtype: bool
        """
        user = ModelsRegistry.get_user(user)
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        return self.model.objects.filter(user=user, package_instance=package_instance).exists()


class PackageInstanceUser(models.Model):
    """
    A PackageInstanceUser is a user who is associated with a package instance.
    """
    #: User associated with the package instance
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #: package instance associated with the user
    package_instance = models.ForeignKey('PackageInstance', on_delete=models.CASCADE)

    #: manager for the PackageInstanceUser class
    objects = PackageInstanceUserManager()

    def __str__(self):
        return f"PackageInstanceUser {self.pk}: \n{self.user}\n{self.package_instance}"


class PackageInstanceManager(models.Manager):
    """
    PackageInstanceManager is a manager for the PackageInstance class
    """

    @transaction.atomic
    def create_package_instance(self,
                                package_source: int | str | PackageSource,
                                commit: str) -> PackageInstance:
        """
        Create a new package instance from the given path

        :param package_source: The package source
        :type package_source: PackageSource
        :param commit: The commit of the package
        :type commit: str

        :return: A new PackageInstance object.
        """
        package_source = ModelsRegistry.get_package_source(package_source)
        package_instance = self.model(package_source=package_source, commit=commit)
        PACKAGES[PackageInstance.commit_msg(package_source, commit)] = Package(package_source.path,
                                                                               commit)
        package_instance.save()
        return package_instance

    def create_source_and_instance(self, name: str, commit: str) -> PackageInstance:
        """
        Create a new package source from the given name. Also create a new package instance for it.
        """
        package_source = PackageSource.objects.create_package_source(name)
        return self.create_package_instance(package_source, commit)

    @transaction.atomic
    def make_package_instance_commit(self, package_instance: int | PackageInstance):
        """
        Create a new package instance from the given path

        :param package_instance: The package instance
        :type package_instance: PackageInstance

        :return: A new PackageInstance object.
        """
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        new_commit = timezone.now().timestamp()

        new_package = package_instance.package.make_commit(new_commit)
        new_package.check_package()

        commit_msg = PackageInstance.commit_msg(package_instance.package_source, new_commit)
        PACKAGES[commit_msg] = new_package

        new_instance = self.model(
            package_source=package_instance.package_source,
            commit=new_commit
        )
        new_instance.save()

        return new_instance

    @transaction.atomic
    def delete_package_instance(self, package_instance: int | PackageInstance):
        """
        If the package instance is not in the database, raise an exception.
        Otherwise, delete the package instance and its package from the database

        :param package_instance: The package instance to delete
        :type package_instance: PackageInstance
        """
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        package_instance.delete()

    def exists_validator(self, pkg_id: int) -> bool:
        """
        If the package with the given ID exists, return True, otherwise return False

        :param pkg_id: The id of the package to check for
        :type pkg_id: int

        :return: A boolean value.
        """
        return self.filter(pk=pkg_id).exists()

class PackageInstance(models.Model):
    """
    A PackageInstance is a unique version of a PackageSource.
    """
    #: foreign key to the PackageSource class :py:class:`PackageSource`
    # This means that each PackageInstance is associated with a single PackageSource
    package_source = models.ForeignKey(PackageSource, on_delete=models.CASCADE)
    #: unique identifier for every package instance
    commit = models.CharField(max_length=2047)

    #: manager for the PackageInstance class
    objects = PackageInstanceManager()

    def __str__(self):
        return f"PackageInstance {self.pk}: \n{self.package_source}\n{self.commit}"

    @classmethod
    def commit_msg(cls, pkg: PackageSource, commit: str) -> str:
        """
        It returns a string that is the name of the package source and the commit

        :param pkg: The package source
        :type pkg: PackageSource
        :param commit: The commit of the package
        :type commit: str

        :return: The name of the package source and the commit.
        """
        return f"{pkg.name}.{commit}"

    @property
    def key(self) -> str:
        """
        It returns a string that is the name of the package source and the commit

        :return: The name of the package source and the commit.
        """
        return self.commit_msg(self.package_source, self.commit)

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

    @property
    def is_used(self) -> bool:
        """
        Checks if package instance is used in any task of any course.

        :return: True if package instance is used in any task, False otherwise.
        :rtype: bool
        """
        from course.models import Task
        return Task.check_instance(self)

    def delete(self, using=None, keep_parents=False):
        """
        If the task is not in the database, raise an exception.
        Otherwise, delete the task and its package from the database

        :raises ValidationError: If the package instance is used in any task
        """
        if self.is_used:
            raise ValidationError('Package is used and you cannot delete it')

        with transaction.atomic():
            # deleting instance in source directory
            self.package.delete()
            PACKAGES.pop(self.key)
            # self delete instance
            super().delete(using, keep_parents)

    def share(self, user: User):
        """
        It creates a new instance of a package, and then creates a new PackageInstanceUser object that links
        the new package instance to the user

        :param user: The user to share the package with
        :type user: User
        """
        new_instance = self.objects.make_package_instance_commit(self)
        PackageInstanceUser.objects.create(user=user, package_instance=new_instance)

    def check_user(self, user: int | str | User) -> bool:
        """
        Checks if user is associated with package instance.

        :param user: The user to be checked
        :type user: int | str | User

        :return: True if user is associated with package instance, False otherwise.
        :rtype: bool
        """
        return PackageInstanceUser.objects.check_user(user, self)
