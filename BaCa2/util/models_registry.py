from __future__ import annotations

from typing import (TYPE_CHECKING, List, Union)

from django.db.models import QuerySet

if TYPE_CHECKING:
    from django.contrib.auth.models import (Group, Permission)
    from main.models import (User, Course)


class ModelsRegistry:
    """
    Helper class used to retrieve models from the database using different possible parameters.
    It stores in one place all logic necessary to allow methods across the project to accept
    different types of parameters which can be used as univocal identifiers of a model instance or
    instances.
    """

    # ------------------------------- django.contrib.auth models ------------------------------- #

    @staticmethod
    def get_group(group: str | int | Group) -> Group:
        """
        Returns a Group model instance from the database using its name or id as a reference.
        It can also be used to return the same instance if it is passed as the parameter (for ease
        of use in case of methods which accept both model instances and their identifiers).

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
    def get_group_id(group: str | int | Group) -> int:
        """
        Returns a group's id from the database using a model instance or its name as a reference.
        It can also be used to return the same id if it is passed as the parameter (for ease of use
        in case of methods which accept both model instances and their identifiers).

        :param group: Group model instance, its name or id.
        :type group: str | int | Group

        :return: Given group's id.
        :rtype: int
        """
        from django.contrib.auth.models import Group

        if isinstance(group, str):
            return Group.objects.get(name=group).id
        if isinstance(group, Group):
            return group.id
        return group

    @staticmethod
    def get_groups(groups: List[str] | List[int] | List[Group]) -> QuerySet[Group] | List[Group]:
        """
        Returns a QuerySet of groups using a list of their names or ids as a reference.
        It can also be used to return a list of Group model instances if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param groups: List of Group model instances, their names or ids.
        :type groups: List[Group] | List[str] | List[int]

        :return: QuerySet of Group model instances or list of Group model instances.
        :rtype: QuerySet[Group] | List[Group]
        """
        from django.contrib.auth.models import Group

        if isinstance(groups[0], str):
            return Group.objects.filter(name__in=groups)
        if isinstance(groups[0], int):
            return Group.objects.filter(id__in=groups)
        return groups

    @staticmethod
    def get_permission(permission: str | int | Permission) -> Permission:
        """
        Returns a Permission model instance from the database using its codename or id as a
        reference. It can also be used to return the same instance if it is passed as the parameter
        (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param permission: Permission model instance, its codename or id.
        :type permission: str | int | Permission

        :return: Permission model instance.
        :rtype: Permission
        """
        from django.contrib.auth.models import Permission

        if isinstance(permission, str):
            return Permission.objects.get(codename=permission)
        if isinstance(permission, int):
            return Permission.objects.get(id=permission)
        return permission

    @staticmethod
    def get_permission_id(permission: str | int | Permission) -> int:
        """
        Returns a permission's id from the database using a model instance or its codename as a
        reference. It can also be used to return the same id if it is passed as the parameter (for
        ease of use in case of methods which accept both model instances and their identifiers).

        :param permission: Permission model instance, its codename or id.
        :type permission: str | int | Permission

        :return: Given permission's id.
        :rtype: int
        """
        from django.contrib.auth.models import Permission

        if isinstance(permission, str):
            return Permission.objects.get(codename=permission).id
        if isinstance(permission, Permission):
            return permission.id
        return permission

    @staticmethod
    def get_permissions(permissions: List[str] | List[int] | List[Permission]
                        ) -> QuerySet[Permission] | List[Permission]:
        """
        Returns a QuerySet of permissions using a list of their codenames or ids as a reference.
        It can also be used to return a list of Permission model instances if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param permissions: List of Permission model instances, their codenames or ids.
        :type permissions: List[Permission] | List[str] | List[int]

        :return: QuerySet of Permission model instances or list of Permission model instances.
        :rtype: QuerySet[Permission] | List[Permission]
        """
        from django.contrib.auth.models import Permission

        if isinstance(permissions[0], str):
            return Permission.objects.filter(codename__in=permissions)
        if isinstance(permissions[0], int):
            return Permission.objects.filter(id__in=permissions)
        return permissions

    # --------------------------------------- main models -------------------------------------- #

    @staticmethod
    def get_user(user: str | int | User) -> User:
        """
        Returns a User model instance from the database using its email or id as a reference.
        It can also be used to return the same instance if it is passed as the parameter (for ease
        of use in case of methods which accept both model instances and their identifiers).

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

    @staticmethod
    def get_user_id(user: str | int | User) -> int:
        """
        Returns a user's id from the database using a model instance or its email as a reference.
        It can also be used to return the same id if it is passed as the parameter (for ease of use
        in case of methods which accept both model instances and their identifiers).

        :param user: User model instance, its email or id.
        :type user: str | int | User

        :return: Given user's id.
        :rtype: int
        """
        from main.models import User

        if isinstance(user, str):
            return User.objects.get(email=user).id
        if isinstance(user, User):
            return user.id
        return user

    @staticmethod
    def get_users(users: List[str] | List[int] | List[User]) -> QuerySet[User] | List[User]:
        """
        Returns a QuerySet of users using a list of their emails or ids as a reference.
        It can also be used to return a list of User model instances if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param users: List of User model instances, their emails or ids.
        :type users: List[User] | List[str] | List[int]

        :return: QuerySet of User model instances or list of User model instances.
        :rtype: QuerySet[User] | List[User]
        """
        from main.models import User

        if isinstance(users[0], str):
            return User.objects.filter(email__in=users)
        if isinstance(users[0], int):
            return User.objects.filter(id__in=users)
        return users

    @staticmethod
    def get_course(course: str | int | Course) -> Course:
        """
        Returns a Course model instance from the database using its short name or id as a reference.
        It can also be used to return the same instance if it is passed as the parameter (for ease
        of use in case of methods which accept both model instances and their identifiers).

        :param course: Course model instance, its short name or id.
        :type course: str | int | Course

        :return: Course model instance.
        :rtype: Course
        """
        from main.models import Course

        if isinstance(course, str):
            return Course.objects.get(short_name=course)
        if isinstance(course, int):
            return Course.objects.get(id=course)
        return course

    @staticmethod
    def get_course_id(course: str | int | Course) -> int:
        """
        Returns a course's id from the database using a model instance or its short name as a
        reference. It can also be used to return the same id if it is passed as the parameter (for
        ease of use in case of methods which accept both model instances and their identifiers).

        :param course: Course model instance, its short name or id.
        :type course: str | int | Course

        :return: Given course's id.
        :rtype: int
        """
        from main.models import Course

        if isinstance(course, str):
            return Course.objects.get(short_name=course).id
        if isinstance(course, Course):
            return course.id
        return course

    @staticmethod
    def get_courses(courses: List[str] | List[int] | List[Course]
                    ) -> QuerySet[Course] | List[Course]:
        """
        Returns a QuerySet of courses using a list of their short names or ids as a reference.
        It can also be used to return a list of Course model instances if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param courses: List of Course model instances, their short names or ids.
        :type courses: List[Course] | List[str] | List[int]

        :return: QuerySet of Course model instances or list of Course model instances.
        :rtype: QuerySet[Course] | List[Course]
        """
        from main.models import Course

        if isinstance(courses[0], str):
            return Course.objects.filter(short_name__in=courses)
        if isinstance(courses[0], int):
            return Course.objects.filter(id__in=courses)
        return courses
