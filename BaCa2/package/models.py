from __future__ import annotations

from pathlib import Path
from typing import List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from baca2PackageManager import Package
from baca2PackageManager.validators import isStr
from core.tools.files import DocFileHandler
from core.tools.misc import random_id
from main.models import User
from util.models_registry import ModelsRegistry


class PackageSourceManager(models.Manager):
    """
    PackageSourceManager is a manager for the PackageSource class
    """

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
        if not package_source.path.exists():
            package_source.path.mkdir()
        return package_source

    @transaction.atomic
    def create_package_source_from_zip(
        self,
        name: str,
        zip_file: Path,
        creator: int | str | User = None,
        safe_name: bool = True,
        return_package_instance: bool = False
    ) -> PackageSource | PackageInstance:
        """
        Create a new package source from the given zip file

        :param name: The name of the package source
        :type name: str
        :param zip_file: The path to the zip file
        :type zip_file: Path
        :param creator: The creator of the package (optional)
        :type creator: int | str | User
        :param safe_name: If True, make the name unique
        :type safe_name: bool
        :param return_package_instance: If True, return the package instance instead of the package
            source
        :type return_package_instance: bool

        :return: A new PackageSource object.
        """
        if safe_name:
            name = name.replace(' ', '_')
            name = f'{name}_{random_id()}'
        package_source = self.model(name=name)
        package_source.save()
        if not package_source.path.exists():
            package_source.path.mkdir()
        package_instance = PackageInstance.objects.create_package_instance_from_zip(
            package_source,
            zip_file
        )
        package_instance.save()
        if creator:
            PackageInstanceUser.objects.create_package_instance_user(creator, package_instance)

        if return_package_instance:
            return package_instance
        return package_source

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
    MAIN_SOURCE = settings.PACKAGES_DIR
    #: name of the package
    name = models.CharField(max_length=511, validators=[isStr])

    #: manager for the PackageSource class
    objects = PackageSourceManager()

    def __str__(self):
        return f'Package {self.pk}: {self.name}'

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
        package_instance_user = self.model.objects.filter(user=user,
                                                          package_instance=package_instance)
        if package_instance_user.exists():
            return package_instance_user.first()
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
        return f'PackageInstanceUser {self.pk}: \n{self.user}\n{self.package_instance}'


class PackageInstanceManager(models.Manager):
    """
    PackageInstanceManager is a manager for the PackageInstance class
    """

    @transaction.atomic
    def create_package_instance(self,
                                package_source: int | str | PackageSource,
                                commit: str,
                                creator: int | str | User = None) -> PackageInstance:
        """
        Create a new package instance from the given path

        :param package_source: The package source
        :type package_source: PackageSource
        :param commit: The commit of the package
        :type commit: str
        :param creator: The creator of the package (optional)
        :type creator: int | str | User

        :return: A new PackageInstance object.
        """
        package_source = ModelsRegistry.get_package_source(package_source)
        package_instance = self.model(package_source=package_source, commit=commit)
        settings.PACKAGES[PackageInstance.commit_msg(package_source, commit)] = Package(
            package_source.path,
            commit)
        package_instance.save()
        if creator:
            PackageInstanceUser.objects.create_package_instance_user(creator, package_instance)
        return package_instance

    @transaction.atomic
    def create_source_and_instance(self,
                                   name: str,
                                   commit: str,
                                   creator: int | str | User = None) -> PackageInstance:
        """
        Create a new package source from the given name. Also create a new package instance for it.

        :param name: The name of the package source
        :type name: str
        :param commit: The commit of the package
        :type commit: str
        :param creator: The creator of the package (optional)
        :type creator: int | str | User

        :return: A new PackageInstance object.
        :rtype: PackageInstance
        """
        package_source = PackageSource.objects.create_package_source(name)
        return self.create_package_instance(package_source, commit, creator)

    @transaction.atomic
    def make_package_instance_commit(self,
                                     package_instance: int | PackageInstance,
                                     copy_permissions: bool = True,
                                     creator: int | str | User = None) -> PackageInstance:
        """
        Create a new package instance from the given path

        :param package_instance: The package instance
        :type package_instance: PackageInstance
        :param copy_permissions: If True, copy the permissions from the old package instance
        :type copy_permissions: bool
        :param creator: The creator of the package (optional)
        :type creator: int | str | User

        :return: A new PackageInstance object.
        """
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        new_commit = f'{timezone.now().timestamp()}'

        new_package = package_instance.package.make_commit(new_commit)
        new_package.check_package()

        commit_msg = PackageInstance.commit_msg(package_instance.package_source, new_commit)
        settings.PACKAGES[commit_msg] = new_package

        try:
            pdf_docs = new_package.doc_path('pdf')
            doc = DocFileHandler(pdf_docs, 'pdf')
            static_path = doc.save_as_static()
        except FileNotFoundError:
            static_path = None

        try:
            new_instance = self.model(
                package_source=package_instance.package_source,
                commit=new_commit,
                pdf_docs=static_path
            )
            new_instance.save()

            if copy_permissions:
                for user in package_instance.permitted_users:
                    new_instance.add_permitted_user(user)
            elif creator:
                PackageInstanceUser.objects.create_package_instance_user(creator, new_instance)

            return new_instance
        except Exception as e:
            DocFileHandler.delete_doc(static_path)
            raise e

    @transaction.atomic
    def delete_package_instance(self,
                                package_instance: int | PackageInstance,
                                delete_files: bool = False):
        """
        If the package instance is not in the database, raise an exception.
        Otherwise, delete the package instance and its package from the database

        :param package_instance: The package instance to delete
        :type package_instance: int | PackageInstance
        :param delete_files: If True, delete the files associated with the package instance
        :type delete_files: bool
        """
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        package_instance.delete(delete_files)

    @transaction.atomic
    def create_package_instance_from_zip(self,
                                         package_source: int | str | PackageSource,
                                         zip_file: Path,
                                         overwrite: bool = False,
                                         permissions_from_instance: int | PackageInstance = None,
                                         creator: int | str | User = None) -> PackageInstance:
        """
        Create a new package instance from the given path

        :param package_source: The package source
        :type package_source: PackageSource
        :param zip_file: The path to the zip file
        :type zip_file: Path
        :param overwrite: If True, overwrite the package instance files if it already exists
        :type overwrite: bool
        :param permissions_from_instance: The package instance to copy the permissions from
            (optional)
        :type permissions_from_instance: int | PackageInstance
        :param creator: The creator of the package (optional)
        :type creator: int | str | User

        :return: A new PackageInstance object.
        """
        package_source = ModelsRegistry.get_package_source(package_source)
        commit_name = f'from_zip_{random_id()}'
        pkg = Package.create_from_zip(package_source.path, commit_name, zip_file, overwrite)
        settings.PACKAGES[PackageInstance.commit_msg(package_source, commit_name)] = pkg

        try:
            pdf_docs = pkg.doc_path('pdf')
            doc = DocFileHandler(pdf_docs, 'pdf')
            static_path = doc.save_as_static()
        except FileNotFoundError:
            static_path = None
        try:
            package_instance = self.model(
                package_source=package_source,
                commit=commit_name,
                pdf_docs=static_path
            )

            package_instance.save()
            if permissions_from_instance:
                permissions_from_instance = ModelsRegistry.get_package_instance(
                    permissions_from_instance)
                for user in permissions_from_instance.permitted_users:
                    PackageInstanceUser.objects.create_package_instance_user(user, package_instance)
            if creator:
                PackageInstanceUser.objects.create_package_instance_user(creator, package_instance)
            return package_instance
        except Exception as e:
            DocFileHandler.delete_doc(static_path)
            raise e

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
    #: pdf docs file path
    pdf_docs = models.FilePathField(path=settings.TASK_DESCRIPTIONS_DIR, null=True, blank=True,
                                    default=None, max_length=2047)

    #: manager for the PackageInstance class
    objects = PackageInstanceManager()

    def __str__(self):
        return f'PackageInstance {self.pk}: \n{self.package_source}\n{self.commit}'

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
        return f'{pkg.name}.{commit}'

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
        return settings.PACKAGES.get(package_id)

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

    @property
    def pdf_docs_path(self) -> Path:
        """
        It returns the path to the pdf docs file

        :return: The path to the pdf docs file.
        """
        return Path(str(self.pdf_docs))

    def delete(self, delete_files: bool = False, using=None, keep_parents=False):
        """
        If the task is not in the database, raise an exception.
        Otherwise, delete the task and its package from the database

        :param delete_files: If True, delete the files associated with the package instance
        :type delete_files: bool

        :raises ValidationError: If the package instance is used in any task
        """
        if self.is_used:
            raise ValidationError('Package is used and you cannot delete it')

        with transaction.atomic():
            # deleting instance in source directory
            if delete_files:
                self.package.delete()
            if self.pdf_docs:
                DocFileHandler.delete_doc(Path(self.pdf_docs))
            settings.PACKAGES.pop(self.key)
            # self delete instance
            super().delete(using, keep_parents)

    @property
    def permitted_users(self) -> List[User]:
        """
        It returns the users that have permissions to the package instance

        :return: The users that have permissions to the package instance.
        """
        pkg_instance_users = PackageInstanceUser.objects.filter(package_instance=self)
        return [pkg_instance_user.user for pkg_instance_user in pkg_instance_users]

    @transaction.atomic
    def add_permitted_user(self, user: int | str | User) -> None:
        """
        It adds a user to the package instance

        :param user: The user to add
        :type user: User
        """
        PackageInstanceUser.objects.create_package_instance_user(user, self)

    def check_user(self, user: int | str | User) -> bool:
        """
        Checks if user is associated with package instance.

        :param user: The user to be checked
        :type user: int | str | User

        :return: True if user is associated with package instance, False otherwise.
        :rtype: bool
        """
        return PackageInstanceUser.objects.check_user(user, self)
