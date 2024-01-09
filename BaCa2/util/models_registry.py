from __future__ import annotations

from pathlib import Path

from typing import (TYPE_CHECKING, List)

from django.db.models import QuerySet

from course.routing import OptionalInCourse

if TYPE_CHECKING:
    from django.contrib.auth.models import (Group, Permission)
    from main.models import (User, Course, Role, RolePreset)
    from course.models import (Round, Task, Submit, Test, TestSet)
    from package.models import PackageSource, PackageInstance
    from BaCa2.choices import TaskJudgingMode


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

    @staticmethod
    def get_role(role: str | int | Role, course: str | int | Course = None) -> Role:
        """
        Returns a Role model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param role: Role name, id or model instance.
        :type role: str | int | Role
        :param course: Course short name, id or model instance.
        :type course: str | int | Course

        :return: Role model instance.
        :rtype: Role

        :raises ValueError: If the role name is passed as a parameter but its course is not.
        """
        from main.models import Role

        if isinstance(role, str):
            if not course:
                raise ValueError('If the role name is passed as a parameter, its course name must '
                                 'be passed as well. A role name is only unique within a course.')
            return Role.objects.get(name=role, course=ModelsRegistry.get_course(course))

        if isinstance(role, int):
            return Role.objects.get(id=role)
        return role

    @staticmethod
    def get_roles(roles: List[str] | List[int] | List[Role],
                  course: str | int | Course = None) -> QuerySet[Role] | List[Role]:
        """
        Returns a QuerySet of roles using a list of their ids or names and course as a reference.
        It can also be used to return a list of Role model instances if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param roles: List of Role names, ids or model instances.
        :type roles: List[str] | List[Role] | List[int]
        :param course: Course short name, id or model instance.
        :type course: str | int | Course

        :return: QuerySet of Role model instances or list of Role model instances.
        :rtype: QuerySet[Role] | List[Role]

        :raises ValueError: If the role names are passed as a parameter but their course is not.
        """
        from main.models import Role

        if isinstance(roles[0], str):
            if not course:
                raise ValueError('If the role names are passed as a parameter, their course name '
                                 'must be passed as well. A role name is only unique within a '
                                 'course.')
            return Role.objects.filter(name__in=roles, course=ModelsRegistry.get_course(course))

        if isinstance(roles[0], int):
            return Role.objects.filter(id__in=roles)
        return roles

    @staticmethod
    def get_role_preset(preset: int | RolePreset) -> RolePreset:
        """
        Returns a RolePreset model instance from the database using its id as a reference. It can
        also be used to return the same instance if it is passed as the parameter (for ease of use
        in case of methods which accept both model instances and their identifiers).

        :param preset: RolePreset id or model instance.
        :type preset: int | RolePreset

        :return: RolePreset model instance.
        :rtype: RolePreset
        """
        from main.models import RolePreset

        if isinstance(preset, int):
            return RolePreset.objects.get(id=preset)
        return preset

    # ------------------------------------package models --------------------------------------- #

    @staticmethod
    def get_package_source(pkg_source: str | int | PackageSource) -> PackageSource:
        """
        Returns a PackageSource model instance from the database using its name or id as a
        reference. It can also be used to return the same instance if it is passed as the parameter
        (for ease of use in case of methods which accept both model instances and their
        identifiers).

        :param pkg_source: PackageSource model instance, its name or id.
        :type pkg_source: str | int | PackageSource

        :return: PackageSource model instance.
        :rtype: PackageSource
        """
        from package.models import PackageSource

        if isinstance(pkg_source, str):
            return PackageSource.objects.get(name=pkg_source)
        if isinstance(pkg_source, int):
            return PackageSource.objects.get(id=pkg_source)
        return pkg_source

    @staticmethod
    def get_package_instance(pkg_instance: int | PackageInstance) -> PackageInstance:
        """
        Returns a PackageInstance model instance from the database using its id as a reference. It
        can also be used to return the same instance if it is passed as the parameter (for ease
        of use in case of methods which accept both model instances and their identifiers).

        :param pkg_instance: PackageInstance id or model instance.
        :type pkg_instance: int | PackageInstance

        :return: PackageInstance model instance.
        :rtype: PackageInstance
        """
        from package.models import PackageInstance

        if isinstance(pkg_instance, int):
            return PackageInstance.objects.get(id=pkg_instance)
        return pkg_instance

    # -------------------------------------- course models ------------------------------------- #

    @staticmethod
    def get_round(round_: int | Round, course: str | int | Course = None) -> Round:
        """
        Returns a Round model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers). If course is not passed as a parameter, it has to be available in context (
        in that case this method should be used inside ``with InCourse(<course>):``).

        :param round_: Round name, id or model instance.
        :type round_: str | int | Round
        :param course: Course short name, id or model instance.
        :type course: str | int | Course

        :return: Round model instance.
        :rtype: Round
        """
        from course.models import Round

        with OptionalInCourse(course):
            if isinstance(round_, int):
                return Round.objects.get(id=round_)
        return round_

    @staticmethod
    def get_rounds(
            rounds: List[int] | List[Round],
            course: str | int | Course = None,
            return_queryset: bool = False
    ) -> QuerySet[Round] | List[Round]:
        """
        Returns a QuerySet of rounds using a list of their ids or model instances and course as a
        reference. It can also be used to return a list of Round model instances if it is passed as
        the parameter (for ease of use in case of methods which accept both model instances and
        their identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param rounds: List of Round names, ids or model instances.
        :type rounds: List[int] | List[Round]
        :param course: Course short name, id or model instance.
        :type course: str | int | Course
        :param return_queryset: If True, returns a QuerySet of Round model instances. Otherwise,
            returns a list of Round model instances.
        :type return_queryset: bool

        :return: QuerySet of Round model instances or list of Round model instances.
        :rtype: QuerySet[Round] | List[Round]
        """
        from course.models import Round

        with OptionalInCourse(course):
            if isinstance(rounds[0], int):
                rounds = Round.objects.filter(id__in=rounds)
                if return_queryset:
                    return rounds
                else:
                    return list(rounds)
        return rounds

    @staticmethod
    def get_task(task: int | Task, course: str | int | Course = None) -> Task:
        """
        Returns a Task model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param task: Task name, id or model instance.
        :type task: str | int | Task
        :param course: Course short name, id or model instance.
        :type course: str | int | Course

        :return: Task model instance.
        :rtype: Task
        """
        from course.models import Task

        with OptionalInCourse(course):
            if isinstance(task, int):
                return Task.objects.get(id=task)
        return task

    @staticmethod
    def get_tasks(
            tasks: List[int] | List[Task],
            course: str | int | Course = None,
            return_queryset: bool = False
    ) -> QuerySet[Task] | List[Task]:
        """
        Returns a QuerySet of tasks using a list of their ids or model instances and course as a
        reference. It can also be used to return a list of Task model instances if it is passed as
        the parameter (for ease of use in case of methods which accept both model instances and
        their identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param tasks: List of Task names, ids or model instances.
        :type tasks: List[int] | List[Task]
        :param course: Course short name, id or model instance.
        :type course: str | int | Course
        :param return_queryset: If True, returns a QuerySet of Task model instances. Otherwise,
            returns a list of Task model instances.
        :type return_queryset: bool

        :return: QuerySet of Task model instances or list of Task model instances.
        :rtype: QuerySet[Task] | List[Task]
        """
        from course.models import Task

        with OptionalInCourse(course):
            if isinstance(tasks[0], int):
                tasks = Task.objects.filter(id__in=tasks)
                if return_queryset:
                    return tasks
                else:
                    return list(tasks)
        return tasks

    @staticmethod
    def get_submit(submit: int | Task, course: str | int | Course = None) -> Submit:
        """
        Returns a Submit model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param submit: Submit name, id or model instance.
        :type submit: str | int | Submit
        :param course: Course short name, id or model instance.
        :type course: str | int | Course

        :return: Submit model instance.
        :rtype: Submit
        """
        from course.models import Submit

        with OptionalInCourse(course):
            if isinstance(submit, int):
                return Submit.objects.get(id=submit)
        return submit

    @staticmethod
    def get_task_judging_mode(judging_mode: str | TaskJudgingMode) -> TaskJudgingMode:
        """
        Returns a TaskJudgingMode model instance from the database using its name as a reference.
        It can also be used to return the same instance if it is passed as the parameter (for ease
        of use in case of methods which accept both model instances and their identifiers).

        :param judging_mode: TaskJudgingMode name or model instance.
        :type judging_mode: str | TaskJudgingMode

        :return: TaskJudgingMode model instance.
        :rtype: TaskJudgingMode
        """
        from BaCa2.choices import TaskJudgingMode

        if isinstance(judging_mode, str):
            judging_mode = judging_mode.upper()
            for mode in list(TaskJudgingMode):
                if mode.value == judging_mode:
                    return mode
        return judging_mode

    @staticmethod
    def get_test_set(test_set: int | TestSet, course: str | int | Course = None) -> TestSet:
        """
        Returns a TestSet model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param test_set: TestSet name, id or model instance.
        :type test_set: str | int | TestSet
        :param course: Course short name, id or model instance.
        :type course: str | int | Course

        :return: TestSet model instance.
        :rtype: TestSet
        """
        from course.models import TestSet

        with OptionalInCourse(course):
            if isinstance(test_set, int):
                return TestSet.objects.get(id=test_set)
        return test_set

    @staticmethod
    def get_test(test: int | Test, course: str | int | Test = None) -> Test:
        """
        Returns a Test model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param test: Test name, id or model instance.
        :type test: str | int | Test
        :param course: Course short name, id or model instance.
        :type course: str | int | Test

        :return: Test model instance.
        :rtype: Test
        """
        from course.models import Test

        with OptionalInCourse(course):
            if isinstance(test, int):
                return Test.objects.get(id=test)
        return test

    @staticmethod
    def get_result(result: int | Test, course: str | int | Test = None) -> Test:
        """
        Returns a Result model instance from the database using its id or name and course as
        a reference. It can also be used to return the same instance if it is passed as the
        parameter (for ease of use in case of methods which accept both model instances and their
        identifiers). If course is not passed as a parameter, it has to be available in
        context (in that case this method should be used inside ``with InCourse(<course>):``).

        :param result: Result name, id or model instance.
        :type result: str | int | Result
        :param course: Course short name, id or model instance.
        :type course: str | int | Result

        :return: Result model instance.
        :rtype: Result
        """
        from course.models import Result

        with OptionalInCourse(course):
            if isinstance(result, int):
                return Result.objects.get(id=result)
        return result

    @staticmethod
    def get_source_code(src: str | Path) -> Path:
        """
        Returns a Path object to the source code file.
        :param src: Path to the source code file or its name.
        :return: Path to the source code file.
        """
        from BaCa2.settings import SUBMITS_DIR
        if isinstance(src, str):
            path = Path(src)
            path = path.absolute()
            if not path.is_relative_to(SUBMITS_DIR):
                path = SUBMITS_DIR / src
        else:
            path = src
        if not path.exists():
            raise FileNotFoundError(f'File {path} does not exist.')
        if not path.is_relative_to(SUBMITS_DIR):
            raise FileNotFoundError(f'Path {path} is not a file.')
        return path

    @staticmethod
    def get_result_status(status: str) -> str:
        """
        Returns a result status from the database using its name as a reference.
        It can also be used to return the same status if it is passed as the parameter (for ease
        of use in case of methods which accept both model instances and their identifiers).

        :param status: Result status name or model instance.
        :type status: str | ResultStatus

        :return: ResultStatus model instance.
        :rtype: ResultStatus
        """
        from BaCa2.choices import ResultStatus

        if isinstance(status, str):
            status = status.upper()
            for result_status in list(ResultStatus):
                if result_status.value == status:
                    return result_status
        return status
