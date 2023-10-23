from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import Group
    from main.models import User


class ModelsRegistry:
    """
    Helper class used to retrieve models from the database using different possible parameters.
    It stores in one place all logic necessary to allow methods across the project to accept
    different types of parameters which can be used as univocal identifiers of a model instance or
    instances.
    """

    @staticmethod
    def get_group(group: str | int | Group) -> Group:
        """
        Returns a Group model instance from the database using its name or id as a reference.
        It can also be used to return the same instance if it is passed as a parameter (for ease
        of use in case of methods which accept both model instances or their identifiers).

        :param group: Group model instance, its name or id.
        :type group: str | int | Group

        :return: Group model instance.
        :rtype: Group
        """
        from django.contrib.auth.models import Group

        if isinstance(group, str):
            return Group.objects.get(name=group)
        if isinstance(group, int):
            return Group.objects.get(id=group)
        return group

    @staticmethod
    def get_user(user: str | int | User) -> User:
        """
        Returns a User model instance from the database using its email or id as a reference.
        It can also be used to return the same instance if it is passed as a parameter (for ease
        of use in case of methods which accept both model instances or their identifiers).

        :param user: User model instance, its email or id.
        :type user: str | int | User

        :return: User model instance.
        :rtype: User
        """
        from main.models import User

        if isinstance(user, str):
            return User.objects.get(email=user)
        if isinstance(user, int):
            return User.objects.get(id=user)
        return user
