from __future__ import annotations

from typing import (List, Type, Any, Callable)

from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin,
                                        BaseUserManager,
                                        Group,
                                        Permission,
                                        ContentType)
from django.core.exceptions import ValidationError
from django.db import (models, transaction)
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from BaCa2.choices import (BasicPermissionType, PermissionCheck, ModelAction)
from course.manager import (create_course as create_course_db, delete_course as delete_course_db)
from course.routing import InCourse
from util.models import (model_cls,
                         get_model_permissions,
                         replace_special_symbols)
from util.models_registry import ModelsRegistry


class UserManager(BaseUserManager):
    """
    This class manages the creation of new :py:class:`User` objects. Its methods allow for creation
    of default and superuser user instances.

    This class extends the BaseUserManager provided in  :py:mod:`django.contrib.auth` and replaces
    the default UserManager class.
    """

    @staticmethod
    @transaction.atomic
    def _create_settings() -> 'Settings':
        """
        Create a new user :py:class:`Settings` object.

        :return: New user settings object.
        :rtype: :py:class:`Settings`
        """
        return Settings.objects.create()

    @transaction.atomic
    def _create_user(
            self,
            email: str,
            password: str,
            is_superuser: bool,
            **other_fields
    ) -> 'User':
        """
        Create a new :py:class:`User` object along with its :py:class:`Settings` object. This
        private method is used by the :py:meth:`create_user` and :py:meth:`create_superuser`
        manager methods.

        :param email: New user's email.
        :type email: str
        :param password: New user's password.
        :type password: str
        :param is_staff: Indicates whether the new user has moderation privileges.
        :type is_staff: bool
        :param is_superuser: Indicates whether the new user has all moderation privileges.
        :type is_superuser: bool
        :param other_fields: Values for non-required user model fields.

        :return: The newly created user.
        :rtype: :py:class:`User`
        """
        user = self.model(
            email=self.normalize_email(email),
            is_superuser=is_superuser,
            date_joined=timezone.now(),
            user_settings=self._create_settings(),
            **other_fields
        )
        user.set_password(password)
        user.save(using='default')
        return user

    @transaction.atomic
    def create_user(self, email: str, password: str, **other_fields) -> 'User':
        """
        Create a new :py:class:`User` without moderation privileges.

        :param email: New user's email.
        :type email: str
        :param password: New user's password.
        :type password: str
        :param other_fields: Values for non-required user fields.

        :return: The newly created user.
        :rtype: :py:class:`User`
        """
        return self._create_user(email=email,
                                 password=password,
                                 is_superuser=False,
                                 **other_fields)

    @transaction.atomic
    def create_superuser(self, email: str, password: str, **other_fields) -> User:
        """
        Create a new :py:class:`User` with all moderation privileges.

        :param email: New user's email.
        :type email: str
        :param password: New user's password.
        :type password: str
        :param other_fields: Values for non-required user fields.

        :return: The newly created superuser.
        :rtype: :py:class:`User`
        """
        return self._create_user(email=email,
                                 password=password,
                                 is_superuser=True,
                                 **other_fields)

    @staticmethod
    @transaction.atomic
    def delete_user(user: str | int | User) -> None:
        """
        Delete given :py:class:`User` object along with its :py:class:`Settings` object.

        :param user: The user to delete. Can be specified by its id, email or the user object.
        :type user: str | int | :py:class:`User`
        """
        ModelsRegistry.get_user(user).delete()


class CourseManager(models.Manager):
    """
    This class manages the creation and deletion of :py:class:`Course` objects. It calls on
    :py:mod:`course.manager` methods to create and delete course databases along with corresponding
    course objects in the 'default' database.
    """

    # ------------------------------------ Course creation ------------------------------------- #

    @transaction.atomic
    def create_course(self,
                      name: str,
                      short_name: str = "",
                      usos_course_code: str | None = None,
                      usos_term_code: str | None = None,
                      role_presets: List[RolePreset] = None) -> Course:
        """
        Create a new :py:class:`Course` with given name, short name, USOS code and roles created
        from given presets. A new database for the course is also created which can be accessed
        using the course's short name with :py:class:`course.routing.InCourse`.

        :param name: Name of the new course.
        :type name: str
        :param short_name: Short name of the new course. If no short name is provided, a unique
            short name is generated based on the course name or USOS code (if it's provided). The
            short name can only contain alphanumeric characters and underscores.
        :type short_name: str
        :param usos_course_code: Course code of the course in the USOS system.
        :type usos_course_code: str
        :param usos_term_code: Term code of the course in the USOS system.
        :type usos_term_code: str
        :param role_presets: List of role presets that will be used to set up roles for the new
            course. The first role in the list will be used as the default role for the course.
            In addition, a course will always receive an admin role with all course
            permissions assigned. If no presets are provided the admin role will be the default
            role for the course.

        :return: The newly created course.
        :rtype: Course

        :raises ValidationError: If the name or short name is too short. If either USOS course code
            or USOS term code is provided without the other.
        """
        if (usos_course_code is not None) ^ (usos_term_code is not None):
            raise ValidationError('Both USOS course code and USOS term code must be provided or '
                                  'neither')

        if usos_course_code is not None and usos_term_code is not None:
            self._validate_usos_code(usos_course_code, usos_term_code)

        if len(name) < 5:
            raise ValidationError('Course name must be at least 5 characters long')

        if short_name:
            if len(short_name) < 3:
                raise ValidationError('Short name must be at least 3 characters long')
            short_name = short_name.lower()
        else:
            short_name = self._generate_short_name(name, usos_course_code, usos_term_code)
        self._validate_short_name(short_name)

        if not role_presets:
            role_presets = []

        roles = [Role.objects.create_role_from_preset(preset) for preset in role_presets]
        roles.append(self.create_admin_role())

        create_course_db(short_name)
        course = self.model(
            name=name,
            short_name=short_name,
            USOS_course_code=usos_course_code,
            USOS_term_code=usos_term_code,
            default_role=roles[0],
            admin_role=roles[-1]
        )
        course.save(using='default')
        course.add_roles(roles)
        return course

    @staticmethod
    def create_admin_role() -> Role:
        """
        Create an admin role for a course. The role has all permissions related to all course
        actions assigned to it.

        :return: The admin role.
        :rtype: Role
        """
        admin_role = Role.objects.create_role(name='admin')
        admin_role.add_permissions(Course.CourseAction.labels)
        return admin_role

    # ------------------------------------ Course deletion ------------------------------------- #

    @staticmethod
    @transaction.atomic
    def delete_course(course: Course | str | int) -> None:
        """
        Delete given :py:class:`Course` and its database. In addition, all roles assigned to the
        course will be deleted.

        :param course: The course to delete.
        :type course: Course | str | int
        """
        course = ModelsRegistry.get_course(course)
        course.delete()

    # ----------------------------------- Auxiliary methods ------------------------------------ #

    @staticmethod
    def _validate_short_name(short_name: str) -> None:
        """
        Validate a given short name. A short name is valid if it consists only of alphanumeric
        characters and underscores. It also has to be unique.

        :param short_name: Short name to validate.
        :type short_name: str

        :raises ValidationError: If the short name contains non-alphanumeric characters other than
            underscores or if a course with given short name already exists.
        """
        if any(not (c.isalnum() or c == '_') for c in short_name):
            raise ValidationError('Short name can only contain alphanumeric characters and'
                                  'underscores')
        if Course.objects.filter(short_name=short_name).exists():
            raise ValidationError('A course with this short name already exists')

    @staticmethod
    def _generate_short_name(name: str,
                             usos_course_code: str | None = None,
                             usos_term_code: str | None = None) -> str:
        """
        Generate a unique short name for a :py:class:`Course` based on its name or its USOS code.

        :param name: Name of the course.
        :type name: str
        :param usos_course_code: Subject code of the course in the USOS system.
        :type usos_course_code: str
        :param usos_term_code: Term code of the course in the USOS system.
        :type usos_term_code: str

        :return: Short name for the course.
        :rtype: str

        :raises ValidationError: If a unique short name could not be generated for the course.
        """
        if usos_course_code and usos_term_code:
            short_name = f'{replace_special_symbols(usos_course_code, "_")}__' \
                         f'{replace_special_symbols(usos_term_code, "_")}'
            short_name = short_name.lower()
        else:
            short_name = ""
            for word in name.split():
                short_name += word[0]

            now = timezone.now()
            short_name += f'_{str(now.year)}'
            short_name = short_name.lower()

            if Course.objects.filter(short_name=short_name).exists():
                short_name += '_' + \
                              f'{len(Course.objects.filter(short_name__startswith=short_name)) + 1}'

        if Course.objects.filter(short_name=short_name).exists():
            raise ValidationError('Could not generate a unique short name for the course')

        return short_name

    @staticmethod
    def _validate_usos_code(usos_course_code: str, usos_term_code: str) -> None:
        """
        Validate USOS course and term codes. The codes are valid only if their combination is unique
        across all courses.

        :param usos_course_code: Course code of the course in the USOS system.
        :type usos_course_code: str
        :param usos_term_code: Term code of the course in the USOS system.
        :type usos_term_code: str

        :raises ValidationError: If the USOS codes are invalid.
        """
        if Course.objects.filter(USOS_course_code=usos_course_code,
                                 USOS_term_code=usos_term_code).exists():
            course = Course.objects.get(USOS_course_code=usos_course_code,
                                        USOS_term_code=usos_term_code)
            raise ValidationError(f'Attempted to create a course with the same USOS course and term'
                                  f'codes as the {course} course')


class Course(models.Model):
    """
    This class represents a course in the default database. The short name of the course can be
    used to access the course's database with :py:class:`course.routing.InCourse`. The methods of
    this class deal with managing course database objects, as well as the users assigned to the
    course and their roles within it.
    """

    class CourseMemberError(Exception):
        """
        Exception raised when an error occurs related to course members.
        """
        pass

    class CourseRoleError(Exception):
        """
        Exception raised when an error occurs related to course roles.
        """
        pass

    #: Manager class for the Course model.
    objects = CourseManager()

    # ----------------------------------- Course information ----------------------------------- #

    #: Name of the course.
    name = models.CharField(
        verbose_name=_("course name"),
        max_length=100,
        blank=False
    )
    #: Short name of the course.
    #: Used to access the course's database with :py:class:`course.routing.InCourse`.
    short_name = models.CharField(
        verbose_name=_("course short name"),
        max_length=40,
        unique=True,
        blank=False
    )
    #: Subject code of the course in the USOS system.
    #: Used for automatic assignment of USOS registered users to the course
    USOS_course_code = models.CharField(
        verbose_name=_("Subject code"),
        max_length=20,
        blank=True,
        null=True
    )
    #: Term code of the course in the USOS system.
    #: Used for automatic assignment of USOS registered users to the course
    USOS_term_code = models.CharField(
        verbose_name=_("Term code"),
        max_length=20,
        blank=True,
        null=True
    )

    # ------------------------------------- Course roles --------------------------------------- #

    #: The default role assigned to users within the course, if no other role is specified.
    default_role = models.ForeignKey(
        verbose_name=_("default role"),
        to='Role',
        on_delete=models.RESTRICT,
        null=False,
        blank=False,
        related_name='+'
    )
    #: The admin role for the course. The role has all permissions related to all course models.
    #: This group is automatically created during course creation.
    admin_role = models.ForeignKey(
        verbose_name=_("admin role"),
        to='Role',
        on_delete=models.RESTRICT,
        null=False,
        blank=False,
        related_name='+'
    )

    # -------------------------------- Actions and permissions --------------------------------- #

    class Meta:
        permissions = [
            # Member related permissions
            ('view_course_member', _('Can view course members')),
            ('add_course_member', _('Can add course members')),
            ('remove_course_member', _('Can remove course members')),
            ('change_course_member_role', _('Can change course member\'s role')),
            ('add_course_admin', _('Can add course admins')),

            # Role related permissions
            ('view_course_role', _('Can view course role')),
            ('edit_course_role', _('Can edit course role')),
            ('add_course_role', _('Can add course role')),
            ('delete_course_role', _('Can delete course role')),

            # Task related permissions
            ('view_course_tasks', _('Can view tasks in the course')),
            ('add_course_tasks', _('Can add tasks to the course')),
            ('edit_course_tasks', _('Can edit tasks in the course')),
            ('delete_course_tasks', _('Can delete tasks from the course')),

            # Round related permissions
            ('add_course_rounds', _('Can add rounds to the course')),
            ('edit_course_rounds', _('Can edit rounds in the course')),
            ('delete_course_rounds', _('Can delete rounds from the course')),

            # TODO
        ]

    class BasicAction(ModelAction):
        ADD = 'add', 'add_course'
        DEL = 'delete', 'delete_course'
        EDIT = 'edit', 'change_course'
        VIEW = 'view', 'view_course'

    class CourseAction(ModelAction):
        VIEW_MEMBER = 'view_member', 'view_course_member'
        ADD_MEMBER = 'add_member', 'add_course_member'
        DEL_MEMBER = 'remove_member', 'remove_course_member'
        CHANGE_MEMBER_ROLE = 'change_member_role', 'change_course_member_role'
        ADD_ADMIN = 'add_admin', 'add_course_admin'

        VIEW_ROLE = 'view_role', 'view_course_role'
        EDIT_ROLE = 'edit_role', 'edit_course_role'
        ADD_ROLE = 'add_role', 'add_course_role'
        DEL_ROLE = 'delete_role', 'delete_course_role'

    # ---------------------------------- Course representation --------------------------------- #

    def __str__(self) -> str:
        """
        Returns the string representation of the Course object.

        :return: Short name and name of the course.
        :rtype: str
        """
        return f"{self.short_name}__{self.name}"

    def get_data(self) -> dict:
        """
        Returns the contents of a Course object's fields as a dictionary. Used to send course data
        to the frontend.

        :return: Dictionary containing the course's id, name and short name.
        :rtype: dict
        """
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'USOS_course_code': self.USOS_course_code,
            'USOS_term_code': self.USOS_term_code,
            'default_role': f'{self.default_role}'
        }

    # -------------------------------------- Role getters -------------------------------------- #

    @property
    def course_roles(self) -> QuerySet[Role]:
        """
        Returns a QuerySet of all roles assigned to the course.

        :return: QuerySet of all roles assigned to the course.
        :rtype: QuerySet[Role]
        """
        return Role.objects.filter(course=self)

    def get_role(self, name: str) -> Role:
        """
        Returns the role with given name assigned to the course.

        :param name: Name of the role to return.
        :type name: str

        :return: The role with given name.
        :rtype: Role

        :raises Course.CourseRoleError: If no role with given name is assigned to the course.
        """
        if not self.role_exists(name):
            raise Course.CourseRoleError(f'Course {self} does not have a role with name {name}')
        return ModelsRegistry.get_role(name, self)

    def get_role_permissions(self, role: str | int | Role) -> QuerySet[Permission]:
        """
        Returns the QuerySet of all permissions assigned to a given role.

        :param role: Role to return permissions for. The role can be specified as either the role
            object, its id or its name.
        :type role: Role | str | int

        :return: QuerySet of all permissions assigned to the role.
        :rtype: QuerySet[Permission]
        """
        return ModelsRegistry.get_role(role, self).permissions.all()

    # --------------------------------- Adding/removing roles ---------------------------------- #

    @transaction.atomic
    def add_role(self, role: Role | int) -> None:
        """
        Add a new role to the course if it passes validation.

        :param role: The role to add. The role can be specified as either the role object or its id.
        :type role: Role | int
        """
        role = ModelsRegistry.get_role(role)
        self._validate_new_role(role)
        role.assign_to_course(self)

    @transaction.atomic
    def add_roles(self, roles: List[Role | int]) -> None:
        """
        Add a list of roles to the course if they pass validation.

        :param roles: The roles to add. The roles can be specified as either the role objects or
            their ids.
        :type roles: List[Role | int]
        """
        for role in ModelsRegistry.get_roles(roles):
            self.add_role(role)

    @transaction.atomic
    def create_role(self,
                    name: str,
                    permissions: List[str] | List[int] | List[Permission]) -> None:
        """
        Create a new role for the course with given name and permissions.

        :param name: Name of the new role.
        :type name: str
        :param permissions: List of permissions to assign to the role. The permissions can be
            specified as either the permission objects, their ids or their codenames.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        self.add_role(Role.objects.create_role(name, permissions))

    @transaction.atomic
    def create_role_from_preset(self, preset: int | RolePreset) -> None:
        """
        Create a new role for the course based on a given preset.

        :param preset: The preset to create the role from. The preset can be specified as either
            its id or the preset object.
        :type preset: int | RolePreset
        """
        self.add_role(Role.objects.create_role_from_preset(ModelsRegistry.get_role_preset(preset)))

    @transaction.atomic
    def remove_role(self, role: str | int | Role) -> None:
        """
        Remove a role from the course and delete it. Cannot be used to remove the default role, the
        admin role or a role with users assigned to it.

        :param role: The role to remove. The role can be specified as either the role object, its id
            or its name.
        :type role: Role | str | int

        :raises Course.CourseRoleError: If the role is the default role, the admin role, has
            users assigned to it or does not exist within the course.
        """
        if not self.role_exists(role):
            raise Course.CourseRoleError("Attempted to remove a role that does not exist within "
                                         "the course")

        role = ModelsRegistry.get_role(role, self)

        if role == self.default_role:
            raise Course.CourseRoleError("Default role cannot be removed from the course")
        if role == self.admin_role:
            raise Course.CourseRoleError("Admin role cannot be removed from the course")
        if role.user_set.exists():
            raise Course.CourseRoleError("Cannot remove a role with users assigned to it")

        role.delete()

    # -------------------------------- Editing role permissions -------------------------------- #

    @transaction.atomic
    def change_role_permissions(self,
                                role: str | int | Role,
                                permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Replace the permissions assigned to a role with a given set of permissions. Cannot be used
        to change permissions for the admin role.

        :param role: The role whose permissions are to be changed. The role can be specified as
            either the role object, its id or its name.
        :type role: Role | str | int
        :param permissions: List of permissions to assign to the role. The permissions can be
            specified as either a list of permission objects, their ids or their codenames.
        :type permissions: List[Permission] | List[str] | List[int]

        :raises Course.CourseRoleError: If the role is the admin role or does not exist within the
            course.
        """
        if not self.role_exists(role):
            raise Course.CourseRoleError("Attempted to change permissions for a role that does not"
                                         "exist within the course")

        role = ModelsRegistry.get_role(role, self)

        if role == self.admin_role:
            raise Course.CourseRoleError("Cannot change permissions for the admin role")

        role.change_permissions(permissions)

    @transaction.atomic
    def add_role_permissions(self,
                             role: str | int | Role,
                             permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Add given permissions to a role.

        :param role: The role to add permissions to. The role can be specified as either the role
            object, its id or its name.
        :type role: Role | str | int
        :param permissions: List of permissions to add to the role. The permissions can be
            specified as either a list of permission objects, their ids or their codenames.
        :type permissions: List[Permission] | List[str] | List[int]

        :raises Course.CourseRoleError: If the role does not exist within the course.
        """
        if not self.role_exists(role):
            raise Course.CourseRoleError("Attempted to add permissions to a role that does not "
                                         "exist within the course")

        ModelsRegistry.get_role(role, self).add_permissions(permissions)

    @transaction.atomic
    def remove_role_permissions(self,
                                role: str | int | Role,
                                permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Remove given permissions from a role.

        :param role: The role to remove permissions from. The role can be specified as either the
            role object, its id or its name.
        :type role: Role | str | int
        :param permissions: List of permissions to remove from the role. The permissions can be
            specified as either a list of permission objects, their ids or their codenames.
        :type permissions: List[Permission] | List[str] | List[int]

        :raises Course.CourseRoleError: If the role is the admin role or does not exist within the
            course.
        """
        if not self.role_exists(role):
            raise Course.CourseRoleError("Attempted to remove permissions from a role that does "
                                         "not exist within the course")

        role = ModelsRegistry.get_role(role, self)

        if role == self.admin_role:
            raise Course.CourseRoleError("Cannot remove permissions from the admin role")

        role.remove_permissions(permissions)

    # ------------------------------------- Member getters ------------------------------------- #

    def members(self) -> QuerySet[User]:
        """
        Returns a QuerySet of all users assigned to the course.

        :return: QuerySet of all users assigned to the course.
        :rtype: QuerySet[User]
        """
        return User.objects.filter(roles__course=self)

    def user_role(self, user: str | int | User) -> Role:
        """
        Returns the role of a given user within the course.

        :param user: The user whose role is to be returned. The user can be specified as either
            the user object, its id or its email.

        :return: The role of the user within the course.
        :rtype: Role

        :raises Course.CourseMemberError: If the user is not a member of the course.
        """
        if not self.user_is_member(user):
            raise Course.CourseMemberError("User is not a member of the course")
        return ModelsRegistry.get_user(user).roles.get(course=self)

    # -------------------------------- Adding/removing members --------------------------------- #

    @transaction.atomic
    def add_member(self, user: str | int | User, role: str | int | Role | None = None) -> None:
        """
        Assign given user to the course with given role. If no role is specified, the user is
        assigned to the course with the default role. Cannot be used to assign a user to the admin
        role.

        :param user: The user to be assigned. The user can be specified as either the user object,
            its id or its email.
        :type user: User | str | int
        :param role: The role to assign the user to. If no role is specified, the user is assigned
            to the course with the default role. The role can be specified as either the role
            object, its id or its name.
        :type role: Role | str | int | None

        :raises Course.CourseRoleError: If the role is the admin role or does not exist within the
            course.
        """
        if not self.role_exists(role):
            raise Course.CourseRoleError("Attempted to assign a user to a non-existent role")

        role = ModelsRegistry.get_role(role, self)

        if role == self.admin_role:
            raise Course.CourseRoleError("Cannot assign a user to the admin role using the "
                                         "add_user method. Use add_admin instead.")
        self._validate_new_member(user)
        role.add_member(user)

    @transaction.atomic
    def add_members(self,
                    users: List[str] | List[int] | List[User],
                    role: str | int | Role) -> None:
        """
        Assign given list of users to the course with given role. If no role is specified, the users
        are assigned to the course with the default role. Cannot be used to assign users to the
        admin role.

        :param users: The users to be assigned. The users can be specified as either a list of user
            objects, their ids or their emails.
        :type users: List[User] | List[str] | List[int]
        :param role: The role to assign the users to. If no role is specified, the users are
            assigned to the course with the default role. The role can be specified as either the
            role object, its id or its name.
        :type role: Role | str | int | None
        """
        ModelsRegistry.get_role(role, self).add_members(users)

    @transaction.atomic
    def add_admin(self, user: str | int | User) -> None:
        """
        Add a new member to the course with the admin role.

        :param user: The user to be assigned. The user can be specified as either the user object,
            its id or its email.
        :type user: User | str | int
        """
        self._validate_new_member(user)
        self.admin_role.add_member(user)

    @transaction.atomic
    def add_admins(self, users: List[str] | List[int] | List[User]) -> None:
        """
        Add given list of users to the course with the admin role.

        :param users: The users to be assigned. The users can be specified as either a list of user
            objects, their ids or their emails.
        :type users: List[User] | List[str] | List[int]
        """
        for user in users:
            self._validate_new_member(user)
        self.admin_role.add_members(users)

    @transaction.atomic
    def remove_member(self, user: str | int | User) -> None:
        """
        Remove given user from the course.

        :param user: The user to be removed. The user can be specified as either the user object,
            its id or its email.
        :type user: User | str | int

        :raises Course.CourseMemberError: If the user is not a member of the course.
        """
        if not self.user_is_member(user):
            raise Course.CourseMemberError("Attempted to remove a user who is not a member of the"
                                           "course.")
        if self.user_is_admin(user):
            raise Course.CourseMemberError("Attempted to remove a user from the admin role using "
                                           "the remove_member method. Use remove_admin instead.")

        self.user_role(user).remove_member(user)

    @transaction.atomic
    def remove_members(self, users: List[str] | List[int] | List[User]) -> None:
        """
        Remove given list of users from the course.

        :param users: The users to be removed. The users can be specified as either a list of user
            objects, their ids or their emails.
        :type users: List[User] | List[str] | List[int]
        """
        for user in users:
            self.remove_member(user)

    @transaction.atomic
    def remove_admin(self, user: str | int | User) -> None:
        """
        Remove given user from the course admin role.

        :param user: The user to be removed. The user can be specified as either the user object,
            its id or its email.
        :type user: User | str | int
        """
        if not self.user_is_member(user):
            raise Course.CourseMemberError("Attempted to remove from the admin role a user who is "
                                           "not a member of the course.")
        if not self.user_is_admin(user):
            raise Course.CourseMemberError("Attempted to remove a user from the admin role who is "
                                           "not an admin in the course.")

        self.admin_role.remove_member(user)

    @transaction.atomic
    def remove_admins(self, users: List[str] | List[int] | List[User]) -> None:
        """
        Remove given list of users from the course admin role.

        :param users: The users to be removed. The users can be specified as either a list of user
            objects, their ids or their emails.
        :type users: List[User] | List[str] | List[int]
        """
        self.admin_role.remove_members(users)

    # --------------------------------- Changing member roles ---------------------------------- #

    @transaction.atomic
    def change_member_role(self,
                           user: str | int | User,
                           new_role: str | int | Role) -> None:
        """
        Change the role of a given user within the course. Cannot be used to change the role of a
        user assigned to the admin role or to assign a user to the admin role.

        :param user: The user whose role is to be changed. The user can be specified as either the
            user object, its id or its email.
        :type user: User | str | int
        :param new_role: The role to assign to the user. The role can be specified as either the
            role object, its id or its name.
        :type new_role: Role | str | int

        :raises Course.CourseMemberError: If the user is not a member of the course.
        :raises Course.CourseRoleError: If the role is the admin role, the user is assigned to the
            admin role or the role does not exist within the course.
        """
        if not self.user_is_member(user):
            raise Course.CourseMemberError('Change of role was attempted for a user who is not a '
                                           'member of the course')
        if not self.role_exists(new_role):
            raise Course.CourseRoleError('Attempted to change a member\'s role to a non-existent '
                                         'role')

        new_role = ModelsRegistry.get_role(new_role, self)

        if new_role == self.admin_role:
            raise Course.CourseRoleError('Attempted to change a member\'s role to the admin role')
        if self.user_role(user) == self.admin_role:
            raise Course.CourseRoleError('Attempted to change the role of a member assigned to the'
                                         'admin role')

        self.user_role(user).remove_member(user)
        new_role.add_member(user)

    @transaction.atomic
    def change_members_role(self,
                            users: List[str] | List[int] | List[User],
                            new_role: str | int | Role) -> None:
        """
        Change the role of a given list of users within the course. Cannot be used to change the
        role of users assigned to the admin role or to assign users to the admin role.

        :param users: The users whose role is to be changed. The users can be specified as either
            a list of user objects, their ids or their emails.
        :type users: List[User] | List[str] | List[int]
        :param new_role: The role to assign to the users. The role can be specified as either the
            role object, its id or its name.
        :type new_role: Role | str | int
        """
        users = ModelsRegistry.get_users(users)

        for user in users:
            self.change_member_role(user, new_role)

    @transaction.atomic
    def make_member_admin(self, user: str | int | User) -> None:
        """
        Assign a given user to the admin role. Cannot be used to assign a user who is not a member
        of the course to the admin role.

        :param user: The user to be assigned. The user can be specified as either the user object,
            its id or its email.
        :type user: User | str | int

        :raises Course.CourseMemberError: If the user is not a member of the course.
        """
        if not self.user_is_member(user):
            raise Course.CourseMemberError('Attempted to assign a user who is not a member of the '
                                           'course to the admin role')
        self.user_role(user).remove_member(user)
        self.admin_role.add_member(user)

    @transaction.atomic
    def make_members_admin(self, users: List[str] | List[int] | List[User]) -> None:
        """
        Assign given list of users to the admin role. Cannot be used to assign users who are not
        members of the course to the admin role.

        :param users: The users to be assigned. The users can be specified as either a list of user
            objects, their ids or their emails.
        :type users: List[User] | List[str] | List[int]
        """
        users = ModelsRegistry.get_users(users)

        for user in users:
            self.make_member_admin(user)

    # ---------------------------------------- Checks ------------------------------------------ #

    def role_exists(self, role: Role | str | int) -> bool:
        """
        Check whether a role with given name exists within the course or if a given role is assigned
        to the course.

        :param role: Role to check. The role can be specified as either the role object, its id or
            its name.
        :type role: Role | str | int

        :return: `True` if the role exists within the course, `False` otherwise.
        :rtype: bool
        """
        if isinstance(role, str):
            return self.course_roles.filter(name=role).exists()
        elif isinstance(role, int):
            return self.course_roles.filter(id=role).exists()
        else:
            return self.course_roles.filter(id=role.id).exists()

    def role_has_permission(self,
                            role: Role | str | int,
                            permission: Permission | str | int) -> bool:
        """
        Check whether a given role has a given permission.

        :param role: The role to check. The role can be specified as either the role object, its id
            or its name.
        :type role: Role | str | int
        :param permission: The permission to check for. The permission can be specified as either
            the permission object, its id or its codename.
        :type permission: Permission | str | int

        :return: `True` if the role has the permission, `False` otherwise.
        :rtype: bool
        """
        return ModelsRegistry.get_role(role, self).has_permission(permission)

    def user_is_member(self, user: str | int | User) -> bool:
        """
        Check whether a given user is a member of the course.

        :param user: The user to check. The user can be specified as either the user object, its id
            or its email.

        :return: `True` if the user is a member of the course, `False` otherwise.
        :rtype: bool
        """
        return ModelsRegistry.get_user(user).roles.filter(course=self).exists()

    def user_is_admin(self, user: str | int | User) -> bool:
        """
        Check whether a given user is assigned to the admin role within the course.

        :param user: The user to check. The user can be specified as either the user object, its id
            or its email.

        :return: `True` if the user is assigned to the admin role, `False` otherwise.
        :rtype: bool
        """
        return self.user_has_role(user, self.admin_role)

    def user_has_role(self, user: str | int | User, role: Role | str | int) -> bool:
        """
        Check whether a given user has a given role within the course.

        :param user: The user to check. The user can be specified as either the user object, its id
            or its email.
        :type user: User | str | int
        :param role: The role to check. The role can be specified as either the role object, its id
            or its name.
        :type role: Role | str | int

        :return: `True` if the user has the role, `False` otherwise.
        :rtype: bool
        """
        return self.user_is_member(user) and \
            self.user_role(user) == ModelsRegistry.get_role(role, self)

    # --------------------------------------- Validators --------------------------------------- #

    def _validate_new_role(self, role: Role | int) -> None:
        """
        Check whether a given role can be assigned to the course. Raises an exception if the role
        cannot be assigned.

        :param role: The role to be validated. The role can be specified as either the role object
            or its id.
        :type role: Group | int

        :raises Course.CourseRoleError: If a role with the same name as the new role is already
            assigned to the course or if the new role is already assigned to a course.
        """
        role = ModelsRegistry.get_role(role)
        if role.course is not None:
            raise Course.CourseRoleError(f'Role {role.name} is already assigned to a course')
        if self.role_exists(role.name):
            raise Course.CourseRoleError(f'A role with name {role.name} is already assigned to '
                                         f'the course. Role names must be unique within the scope '
                                         f'of a course.')

    def _validate_new_member(self, user: str | int | User) -> None:
        """
        Check whether a given user can be assigned to the course.\

        :param user: The user to be validated. The user can be specified as either the user object,
            its id or its email.

        :raises Course.CourseMemberError: If the user is already a member of the course.
        """
        if self.user_is_member(user):
            raise Course.CourseMemberError("User is already a member of the course")

    # -------------------------------- Inside course actions ----------------------------------- #

    from course.models import Round, Task, Submit

    @staticmethod
    def inside_course(func: Callable) -> Callable:
        """
        Decorator used to wrap methods that deal with course database objects. The decorator
        ensures that the method is called within the scope of a course database.

        :param func: The method to be wrapped.
        :type func: Callable

        :return: The wrapped method (in course scope)
        :rtype: Callable
        """

        def action(self: Course, *args, **kwargs):
            with InCourse(self):
                return func(*args, **kwargs)

        return action

    # Round actions -------------

    #: Creates a new round in the course using :py:meth:`course.models.Round.objects.create_round`.
    create_round = inside_course(Round.objects.create_round)

    #: Deletes a round from the course using :py:meth:`course.models.Round.objects.delete_round`.
    delete_round = inside_course(Round.objects.delete_round)

    #: Returns a QuerySet of all rounds in the course using
    #: :py:meth:`course.models.Round.objects.all_rounds`.
    rounds = inside_course(Round.objects.all_rounds)

    #: Getter for Round model
    get_round = inside_course(ModelsRegistry.get_round)

    # Task actions --------------

    #: Creates a new task in the course using :py:meth:`course.models.Task.objects.create_task`.
    create_task = inside_course(Task.objects.create_task)

    #: Deletes a task from the course using :py:meth:`course.models.Task.objects.delete_task`.
    delete_task = inside_course(Task.objects.delete_task)

    #: Getter for Task model
    get_task = inside_course(ModelsRegistry.get_task)

    # Submit actions ------------

    #: Creates a new submit in the course using
    #: :py:meth:`course.models.Submit.objects.create_submit`.
    create_submit = inside_course(Submit.objects.create_submit)

    #: Deletes a submit from the course using :py:meth:`course.models.Submit.objects.delete_submit`.
    delete_submit = inside_course(Submit.objects.delete_submit)

    #: Getter for Submit model
    get_submit = inside_course(ModelsRegistry.get_submit)

    # --------------------------------------- Deletion ----------------------------------------- #

    def delete(self, using: Any = None, keep_parents: bool = False) -> None:
        """
        Delete the course, all its roles and its database.
        """
        delete_course_db(self.short_name)
        super().delete(using, keep_parents)


class Settings(models.Model):
    """
    This model represents a user's (:py:class:`User`) settings. It is used to store personal,
    user-specific data pertaining to the website display options, notification preferences, etc.
    """
    #: User's preferred UI theme.
    theme = models.CharField(
        verbose_name=_("UI theme"),
        max_length=255,
        default='dark'
    )


class User(AbstractBaseUser):
    """
    This class stores user information. Its methods can be used to check permissions pertaining to
    the default database models as well as course access and models from course databases.
    The class extends AbstractBaseUser and PermissionsMixin classes provided in django.contrib.auth
    to replace the default User model.
    """

    class UserPermissionError(Exception):
        """
        Exception raised when an error occurs related to user permissions.
        """
        pass

    # ---------------------------------- Personal information ---------------------------------- #

    #: User's email. Used to log in.
    email = models.EmailField(
        verbose_name=_("email address"),
        max_length=255,
        unique=True
    )
    #: User's first name.
    first_name = models.CharField(
        verbose_name=_("first name"),
        max_length=255,
        blank=True
    )
    #: User's last name.
    last_name = models.CharField(
        verbose_name=_("last name"),
        max_length=255,
        blank=True
    )
    #: Date of account creation.
    date_joined = models.DateField(
        verbose_name=_("date joined"),
        auto_now_add=True
    )
    #: User's settings.
    user_settings = models.OneToOneField(
        verbose_name=_("user settings"),
        to=Settings,
        on_delete=models.RESTRICT,
        null=False,
        blank=False
    )

    # ---------------------------------- Authentication data ----------------------------------- #

    #: Indicates whether user has all available moderation privileges.
    is_superuser = models.BooleanField(
        verbose_name=_("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without explicitly assigning them."
        ),
    )
    #: Groups the user belongs to. Groups are used to grant permissions to multiple users at once
    #: and to assign course access and roles to users.
    groups = models.ManyToManyField(
        to=Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions granted to each of "
            "their groups."
        ),
        related_name="user_set",
        related_query_name="user",
    )
    #: Course roles user has been assigned to. Used to check course access and permissions.
    roles = models.ManyToManyField(
        to='Role',
        verbose_name=_("roles"),
        blank=True,
        help_text=_("The course roles this user has been assigned to."),
        related_name="user_set",
        related_query_name="user",
    )
    #: Permissions specifically granted to the user.
    user_permissions = models.ManyToManyField(
        to=Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="user_set",
        related_query_name="user",
    )

    # ------------------------------------ Django settings ------------------------------------- #

    #: Indicates which field should be considered as username.
    #: Required when replacing default Django User model.
    USERNAME_FIELD = 'email'

    #: Indicates which field should be considered as email.
    #: Required when replacing default Django User model.
    EMAIL_FIELD = 'email'

    #: Indicates which fields besides the USERNAME_FIELD are required when creating a User object.
    REQUIRED_FIELDS = []

    #: Manager class for the User model.
    objects = UserManager()

    # ----------------------------------- User representation ---------------------------------- #

    def __str__(self) -> str:
        """
        Returns the string representation of the User object.

        :return: User's email.
        :rtype: str
        """
        return self.email

    def get_data(self) -> dict:
        """
        Returns the contents of a User object's fields as a dictionary. Used to send user data
        to the frontend.

        :return: Dictionary containing the user's data
        :rtype: dict
        """
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_superuser': self.is_superuser,
            'date_joined': self.date_joined,
        }

    # ------------------------------------ Auxiliary Checks ------------------------------------ #

    @classmethod
    def exists(cls, user_id: int) -> bool:
        """
        Check whether a user with given id exists.

        :param user_id: The id of the user in question.
        :type user_id: int

        :return: `True` if user with given id exists, `False` otherwise.
        :rtype: bool
        """

        return cls.objects.exists(pk=user_id)

    def in_group(self, group: Group | str | id) -> bool:
        """
        Check whether the user belongs to a given group.

        :param group: Group to check user's membership in. Can be specified as either the group
            object, its name or its id.
        :type group: Group | str | id

        :return: `True` if the user belongs to the group, `False` otherwise.
        :rtype: bool
        """
        return self.groups.filter(id=ModelsRegistry.get_group_id(group)).exists()

    def can_access_course(self, course: Course | str | int) -> bool:
        """
        Check whether the user has been assigned to a given course.

        :param course: Course to check user's access to. Can be specified as either the course
            object, its short name or its id.
        :type course: Course | str | int

        :return: `True` if user has been assigned to the course, `False` otherwise.
        :rtype: bool
        """
        if Group.objects.filter(
                user=self,
                groupcourse__course=ModelsRegistry.get_course(course)
        ).exists():
            return True
        return False

    # ---------------------------------- Permission editing ----------------------------------- #

    @transaction.atomic
    def add_permission(self, permission: Permission | str | int) -> None:
        """
        Add an individual permission to the user.

        :param permission: Permission to add. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :raises User.UserPermissionError: If the user already has the permission.
        """
        permission = ModelsRegistry.get_permission(permission)

        if self.has_individual_permission(permission):
            raise User.UserPermissionError(f'Attempted to add permission {permission.codename} '
                                           f'to user {self} who already has it')

        self.user_permissions.add(permission)

    @transaction.atomic
    def add_permissions(self, permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Add multiple individual permissions to the user.

        :param permissions: List of permissions to add. The permissions can be specified as either
            the permission objects, their codenames or their ids.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        permissions = ModelsRegistry.get_permissions(permissions)

        for permission in permissions:
            self.add_permission(permission)

    @transaction.atomic
    def remove_permission(self, permission: Permission | str | int) -> None:
        """
        Remove an individual permission from the user.

        :param permission: Permission to remove. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :raises User.UserPermissionError: If the user does not have the permission.
        """
        permission = ModelsRegistry.get_permission(permission)

        if not self.has_individual_permission(permission):
            raise User.UserPermissionError(f'Attempted to remove permission {permission.codename} '
                                           f'from user {self} who does not have it')

        self.user_permissions.remove(permission)

    @transaction.atomic
    def remove_permissions(self, permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Remove multiple individual permissions from the user.

        :param permissions: List of permissions to remove. The permissions can be specified as
            either the permission objects, their codenames or their ids.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        permissions = ModelsRegistry.get_permissions(permissions)

        for permission in permissions:
            self.remove_permission(permission)

    # ------------------------------------ Permission checks ----------------------------------- #

    def has_individual_permission(self, permission: Permission | str | int) -> bool:
        """
        Check whether the user possesses a given permission on an individual level (does not check
        group-level permissions or superuser status).

        :param permission: Permission to check for. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :return: `True` if the user has the permission, `False` otherwise.
        :rtype: bool
        """
        return self.user_permissions.filter(
            id=ModelsRegistry.get_permission_id(permission)
        ).exists()

    def has_group_permission(self, permission: Permission | str | int) -> bool:
        """
        Check whether the user possesses a given permission on a group level (does not check
        individual permissions or superuser status).

        :param permission: Permission to check for. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :return: `True` if the user has the permission, `False` otherwise.
        :rtype: bool
        """
        return self.groups.filter(permissions=ModelsRegistry.get_permission(permission)).exists()

    def has_permission(self, permission: Permission | str | int) -> bool:
        """
        Check whether the user possesses a given permission. The method checks both individual and
        group-level permissions as well as superuser status.

        :param permission: Permission to check for. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :return: `True` if the user has the permission or is a superuser, `False` otherwise.
        :rtype: bool
        """
        if self.is_superuser:
            return True
        return self.has_individual_permission(permission) or \
            self.has_group_permission(permission)

    def has_action_permission(self, action: ModelAction,
                              permission_check: PermissionCheck = PermissionCheck.GEN) -> bool:
        """
        Check whether the user has the permission to perform a given action on model with defined
        model actions. Depending on the type of permission check specified, the method can check
        user-specific permissions, group-level permissions or both (the default option, in this case
        will also check superuser status).

        :param action: Action to check for.
        :type action: ModelAction
        :param permission_check: Type of permission check to perform.
        :type permission_check: PermissionCheck

        :return: `True` if the user has the permission, `False` otherwise. If general permission
            check is performed, the method will also return `True` if the user is a superuser.
        :rtype: bool

        raises ValueError: If the permission_check value is not recognized.
        """
        if permission_check == PermissionCheck.GEN:
            return self.has_permission(action.label)
        elif permission_check == PermissionCheck.INDV:
            return self.has_individual_permission(action.label)
        elif permission_check == PermissionCheck.GRP:
            return self.has_group_permission(action.label)
        raise ValueError(f'Invalid permission check type: {permission_check}')

    def has_basic_model_permissions(self,
                                    model: model_cls,
                                    permissions: BasicPermissionType | List[BasicPermissionType]
                                    = 'all',
                                    permission_check: PermissionCheck
                                    = PermissionCheck.GEN) -> bool:
        """
        Check whether a user possesses a specified basic permission/list of basic permissions for a
        given 'default' database model. Depending on the type of permission check specified, the
        method can check user-specific permissions, group-level permissions or both (the default
        option, in this case will also check superuser status).

        The default permissions option 'all' checks all basic permissions related to the model.
        Basic permissions are the permissions automatically created by Django for each model (add,
        change, delete, view).

        :param model: The model to check permissions for.
        :type model: Type[models.Model]
        :param permissions: Permissions to check for the given model. Permissions can be given as a
            BasicPermissionTypes object/List of objects, the default option 'all' checks all basic
            permissions related to the model.
        :type permissions: BasicPermissionType or List[BasicPermissionTypes]
        :param permission_check: Type of permission check to perform.
        :type permission_check: PermissionCheck

        :returns: `True` if the user possesses the specified permission/s for the given model,
            `False` otherwise. If general permission check is performed, the method will also return
            `True` if the user is a superuser.
        :rtype: bool
        """
        if permission_check == PermissionCheck.GEN and self.is_superuser:
            return True

        permissions = get_model_permissions(model, permissions)
        has_perm = {p: False for p in permissions}

        if permission_check == PermissionCheck.GEN or permission_check == PermissionCheck.GRP:
            for perm in permissions:
                if self.has_group_permission(perm):
                    has_perm[perm] = True
        if permission_check == PermissionCheck.GEN or permission_check == PermissionCheck.INDV:
            for perm in permissions:
                if self.has_individual_permission(perm):
                    has_perm[perm] = True

        return all(has_perm.values())

    def has_course_permission(self,
                              permission: Permission | str | int,
                              course: Course | str | int) -> bool:
        """
        Check whether the user possesses a given permission within a given :py:class:`Course`. Also
        checks superuser status.

        :param permission: Permission to check for. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int
        :param course: Course to check permission for. The course can be specified as either the
            Course object, its short name or its id.
        :type course: Course | str | int

        :returns: `True` if the user has the permission or is superuser, `False` otherwise.
        :rtype: bool
        """
        if self.is_superuser:
            return True
        return ModelsRegistry.get_course(course).user_role(self).has_permission(permission)

    def has_course_action_permission(self, action: ModelAction, course: Course | str | int) -> bool:
        """
        Check whether the user has the permission to perform a given action on model with defined
        model actions within a given :py:class:`Course`. Also checks superuser status.

        :param action: Action to check for.
        :type action: ModelAction
        :param course: Course to check permission for. The course can be specified as either the
            Course object, its short name or its id.
        :type course: Course | str | int

        :return: `True` if the user has the permission or is superuser, `False` otherwise.
        :rtype: bool
        """
        return self.has_course_permission(action.label, course)

    def has_basic_course_model_permissions(
            self,
            model: model_cls,
            course: Course | str | int,
            permissions: BasicPermissionType | List[BasicPermissionType] = 'all'
    ) -> bool:
        """
        Check whether a user possesses a specified permission/list of permissions for a given
        'course' database model. Does not check user-specific permissions or group-level
        permissions, checks only course-level permissions based on the user's role within the
        course and superuser status.

        :param model: The model to check permissions for.
        :type model: Type[models.Model]
        :param course: Course to check permission for. The course can be specified as either the
            Course object, its short name or its id.
        :type course: Course | str | int
        :param permissions: Permissions to check for the given model. Permissions can be given as a
            PermissionTypes object/List of objects, the default option 'all' checks all permissions
            related to the model.
        :type permissions: BasicPermissionType or List[PermissionTypes]

        :returns: `True` if the user possesses the specified permission/s for the given model or
            is a superuser, `False` otherwise.
        :rtype: bool
        """
        if self.is_superuser:
            return True

        permissions = get_model_permissions(model, permissions)

        for p in permissions:
            if not self.has_course_permission(p, ModelsRegistry.get_course(course)):
                return False
        return True

    # ---------------------------------- Permission getters ----------------------------------- #

    def get_individual_permissions(self) -> List[Permission]:
        """
        Returns a list of all individual permissions possessed by the user.

        :returns: List of all individual permissions possessed by the user.
        :rtype: List[Permission]
        """
        return list(self.user_permissions.all())

    def get_group_permissions(self) -> List[Permission]:
        """
        Returns a list of all group-level permissions possessed by the user.

        :returns: List of all group-level permissions possessed by the user.
        :rtype: List[Permission]
        """
        groups = self.groups.all()
        permissions = []
        for group in groups:
            permissions.extend(list(group.permissions.all()))
        return permissions

    def get_permissions(self) -> List[Permission]:
        """
        Returns a list of all permissions possessed by the user, both individual and group-level.

        :returns: List of all permissions possessed by the user.
        :rtype: List[Permission]
        """
        return self.get_individual_permissions() + self.get_group_permissions()

    def get_course_permissions(self, course: Course | str | int) -> List[Permission]:
        """
        Returns a list of all permissions possessed by the user within a given course.

        :param course: Course to check permission for. The course can be specified as either the
            Course object, its short name or its id.
        :type course: Course | str | int

        :returns: List of all permissions possessed by the user within the given course.
        :rtype: List[Permission]
        """
        return ModelsRegistry.get_course(course).user_role(self).permissions.all()

    # --------------------------------------- Deletion ----------------------------------------- #

    def delete(self, using=None, keep_parents=False):
        """
        Delete the user and their settings.
        """
        settings = self.user_settings
        super().delete(using, keep_parents)
        settings.delete()


class RoleManager(models.Manager):
    """
    Manager class for the Role model. Governs the creation of custom and preset roles as well as
    their deletion.
    """

    @transaction.atomic
    def create_role(self,
                    name: str,
                    permissions: List[Permission] | List[str] | List[int] = None,
                    course: Course = None) -> Role:
        """
        Create a new role with given name and permissions assigned to a specified course (if no
        course is specified, the role will be unassigned).

        :param name: Name of the role.
        :type name: str
        :param permissions: Permissions which should be assigned to the role. The permissions can be
            specified as either the permission objects, their codenames or their ids. If no
            permissions are specified, the role will be created without any permissions.
        :type permissions: List[Permission] | List[str] | List[int]
        :param course: Course the role should be assigned to.
        :type course: Course

        :return: The newly created role.
        :rtype: Role
        """
        if not permissions:
            permissions = []
        else:
            permissions = ModelsRegistry.get_permissions(permissions)

        role = self.model(name=name)
        role.save()

        for permission in permissions:
            role.permissions.add(permission)

        if course:
            course.add_role(role)

        return role

    @transaction.atomic
    def create_role_from_preset(self, preset: RolePreset, course: Course = None) -> Role:
        """
        Create a new role from given preset and assign it to a specified course (if no course is
        specified, the role will be unassigned).

        :param preset: Preset to create the role from.
        :type preset: RolePreset
        :param course: Course the role should be assigned to.
        :type course: Course

        :return: The newly created role.
        :rtype: Role
        """
        return self.create_role(
            name=preset.name,
            permissions=[perm for perm in preset.permissions.all()],
            course=course
        )

    @transaction.atomic
    def delete_role(self, role: Role | int) -> None:
        """
        Delete a role.

        :param role: Role to delete. The role can be specified as either the role object or its id.
        :type role: Role | int
        """
        role = ModelsRegistry.get_role(role)
        role.delete()


class Role(models.Model):
    """
    This model represents a role within a course. It is used to assign users to courses and to
    define the permissions they have within the course.
    """

    class RolePermissionError(Exception):
        """
        Exception raised when an error occurs related to role permissions.
        """
        pass

    class RoleMemberError(Exception):
        """
        Exception raised when an error occurs related to role members.
        """
        pass

    #: Name of the role.
    name = models.CharField(
        verbose_name=_("role name"),
        max_length=100,
        blank=False,
        null=False
    )
    #: Permissions assigned to the role.
    permissions = models.ManyToManyField(
        to=Permission,
        verbose_name=_("role permissions"),
        blank=True
    )
    #: Course the role is assigned to. A single role can only be assigned to a single course.
    course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        verbose_name=_("course"),
        related_name='role_set',
        null=True,
    )

    objects = RoleManager()

    def __str__(self) -> str:
        """
        Returns the string representation of the Role object.

        :return: :py:meth:`Course.__str__` representation of the course and the name of the role.
        :rtype: str
        """
        return f'{self.name}_{self.course}'

    def has_permission(self, permission: Permission | str | int) -> bool:
        """
        Check whether the role has a given permission.

        :param permission: Permission to check for. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :return: `True` if the role has the permission, `False` otherwise.
        :rtype: bool
        """
        return self.permissions.filter(id=ModelsRegistry.get_permission_id(permission)).exists()

    @transaction.atomic
    def add_permission(self, permission: Permission | str | int) -> None:
        """
        Add a permission to the role.

        :param permission: Permission to add. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :raises Role.RolePermissionError: If the role already has the permission.
        """
        permission = ModelsRegistry.get_permission(permission)

        if self.has_permission(permission):
            raise Role.RolePermissionError(f'Attempted to add permission {permission.codename} '
                                           f'to role {self} which already has it')

        self.permissions.add(permission)

    @transaction.atomic
    def add_permissions(self, permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Add multiple permissions to the role.

        :param permissions: List of permissions to add. The permissions can be specified as either
            a list of permission objects, their codenames or their ids.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        permissions = ModelsRegistry.get_permissions(permissions)

        for permission in permissions:
            self.add_permission(permission)

    @transaction.atomic
    def remove_permission(self, permission: Permission | str | int) -> None:
        """
        Remove a permission from the role.

        :param permission: Permission to remove. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :raises Role.RolePermissionError: If the role does not have the permission.
        """
        permission = ModelsRegistry.get_permission(permission)

        if not self.has_permission(permission):
            raise Role.RolePermissionError(f'Attempted to remove permission {permission.codename} '
                                           f'from role {self} which does not have it')

        self.permissions.remove(permission)

    @transaction.atomic
    def remove_permissions(self, permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Remove multiple permissions from the role.

        :param permissions: List of permissions to remove. The permissions can be specified as
            either a list of permission objects, their codenames or their ids.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        permissions = ModelsRegistry.get_permissions(permissions)

        for permission in permissions:
            self.remove_permission(permission)

    @transaction.atomic
    def change_permissions(self, permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Change the permissions assigned to the role. All previously assigned permissions will be
        removed and replaced with the new ones.

        :param permissions: List of permissions to add. The permissions can be specified as either
            a list of permission objects, their codenames or their ids.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        self.permissions.clear()
        self.add_permissions(permissions)

    @transaction.atomic
    def assign_to_course(self, course: Course | str | int) -> None:
        """
        Assign the role to a course.

        :param course: Course to assign the role to. The course can be specified as either the
            course object, its short name or its id.
        :type course: Course | str | int

        :raises ValidationError: If the role is already assigned to a course.
        """
        course = ModelsRegistry.get_course(course)
        if self.course is not None:
            raise ValidationError(f'Attempted to assign role {self} to course {course} while it '
                                  f'is already assigned to course {self.course}')
        self.course = course
        self.save()

    def user_is_member(self, user: str | int | User) -> bool:
        """
        Check whether a user is assigned to the role.

        :param user: User to check. The user can be specified as either the user object, its email
            or its id.
        :type user: str | int | User

        :return: `True` if the user is assigned to the role, `False` otherwise.
        :rtype: bool
        """
        return self.user_set.filter(id=ModelsRegistry.get_user_id(user)).exists()

    @transaction.atomic
    def add_member(self, user: str | int | User) -> None:
        """
        Add a user to the role.

        :param user: User to add. The user can be specified as either the user object, its email or
            its id.
        :type user: str | int | User

        :raises Role.RoleMemberError: If the user is already assigned to the role.
        """
        user = ModelsRegistry.get_user(user)

        if self.user_is_member(user):
            raise Role.RoleMemberError(f'Attempted to add user {user} to role {self} who is '
                                       f'already assigned to it')

        self.user_set.add(user)

    @transaction.atomic
    def add_members(self, users: List[str] | List[int] | List[User]) -> None:
        """
        Add multiple users to the role.

        :param users: List of users to add. The users can be specified as either the user objects,
            their emails or their ids.
        :type users: List[str] | List[int] | List[User]
        """
        users = ModelsRegistry.get_users(users)

        for user in users:
            self.add_member(user)

    @transaction.atomic
    def remove_member(self, user: str | int | User) -> None:
        """
        Remove a user from the role.

        :param user: User to remove. The user can be specified as either the user object, its email
            or its id.
        :type user: str | int | User

        :raises Role.RoleMemberError: If the user is not assigned to the role.
        """
        user = ModelsRegistry.get_user(user)

        if not self.user_is_member(user):
            raise Role.RoleMemberError(f'Attempted to remove user {user} from role {self} who is '
                                       f'not assigned to it')

        self.user_set.remove(user)

    @transaction.atomic
    def remove_members(self, users: List[str] | List[int] | List[User]) -> None:
        """
        Remove multiple users from the role.

        :param users: List of users to remove. The users can be specified as either the user
            objects, their emails or their ids.
        :type users: List[str] | List[int] | List[User]
        """
        users = ModelsRegistry.get_users(users)

        for user in users:
            self.remove_member(user)

    @transaction.atomic
    def delete(self) -> None:
        """
        Delete the role.
        """
        self.user_set.clear()
        self.permissions.clear()
        super().delete()


class RolePresetManager(models.Manager):
    """
    Manager class for the RolePreset model. Governs the creation of presets as well as their
    deletion.
    """

    @transaction.atomic
    def create_role_preset(self,
                           name: str,
                           permissions: List[Permission] | List[str] | List[int] = None,
                           public: bool = True,
                           creator: str | int | User = None) -> RolePreset:
        """
        Create a new role preset with given name, permissions, public status and creator.

        :param name: Name of the preset.
        :type name: str
        :param permissions: Permissions which should be assigned to the preset. The permissions can
            be specified as either the permission objects, their codenames or their ids. If no
            permissions are specified, the preset will be created without any permissions.
        :type permissions: List[Permission] | List[str] | List[int]
        :param public: Indicates whether the preset is public. Public presets can be used by all
            users, private presets can only be used by their creator or other users given access.
        :type public: bool
        :param creator: User who created the preset. If no creator is specified, the preset will
            be created without a creator.
        :type creator: str | int | User

        :return: The newly created preset.
        :rtype: RolePreset

        :raises ValidationError: If the name is too short.
        """
        if len(name) < 4:
            raise ValidationError('Preset name must be at least 4 characters long')

        preset = self.model(
            name=name,
            public=public,
            creator=ModelsRegistry.get_user(creator)
        )
        preset.save()
        preset.add_permissions(permissions)
        return preset

    @transaction.atomic
    def delete_role_preset(self, preset: RolePreset | int) -> None:
        """
        Delete a role preset.

        :param preset: Preset to delete. The preset can be specified as either the preset object or
            its id.
        :type preset: RolePreset | int
        """
        preset = ModelsRegistry.get_role_preset(preset)
        preset.delete()


class RolePreset(models.Model):
    """
    This model represents a preset from which a role can be created. Presets contain on creation
    a defined set of permissions and can be used to quickly setup often recurring course roles such
    as student, tutor, etc.
    """

    #: Manager class for the RolePreset model.
    objects = RolePresetManager()

    #: Name of the preset. Will be used as the name of the role created from the preset.
    name = models.CharField(
        verbose_name=_("preset name"),
        max_length=100,
        blank=False,
        null=False
    )
    #: Permissions assigned to the preset. Will be assigned to the role created from the preset.
    permissions = models.ManyToManyField(
        to=Permission,
        verbose_name=_("preset permissions"),
        blank=True
    )
    #: Whether the preset is public. Public presets can be used by all users, private presets can
    # only be used by their creator or other users given access.
    public = models.BooleanField(
        verbose_name=_("preset is public"),
        default=True,
        help_text=_("Indicates whether the preset is public. Public presets can be used by all "
                    "users, private presets can only be used by their creator or other users given "
                    "access.")
    )
    #: User who created the preset.
    creator = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name=_("preset creator"),
        related_name='created_role_presets',
        blank=True,
        null=True
    )

    def __str__(self) -> str:
        """
        Returns the string representation of the RolePreset object.

        :return: Name of the preset.
        :rtype: str
        """
        return self.name

    def get_data(self) -> dict:
        """
        Returns the contents of a RolePreset object's fields as a dictionary. Used to send preset
        data to the frontend.

        :return: Dictionary containing the role preset's data
        :rtype: dict
        """
        return {
            'id': self.id,
            'name': self.name,
            'permissions': [perm.codename for perm in self.permissions.all()],
            'public': self.public,
            'creator': self.creator.email if self.creator else None,
        }

    def has_permission(self, permission: Permission | str | int) -> bool:
        """
        Check whether the preset has a given permission.

        :param permission: Permission to check for. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :return: `True` if the preset has the permission, `False` otherwise.
        :rtype: bool
        """
        return self.permissions.filter(id=ModelsRegistry.get_permission_id(permission)).exists()

    @transaction.atomic
    def add_permission(self, permission: Permission | str | int) -> None:
        """
        Add a permission to the preset.

        :param permission: Permission to add. The permission can be specified as either the
            permission object, its codename or its id.
        :type permission: Permission | str | int

        :raises ValidationError: If the preset already has the permission.
        """
        permission = ModelsRegistry.get_permission(permission)

        if self.has_permission(permission):
            raise ValidationError(f'Attempted to add permission {permission.codename} to preset '
                                  f'{self} which already has it')

        self.permissions.add(permission)

    @transaction.atomic
    def add_permissions(self, permissions: List[Permission] | List[str] | List[int]) -> None:
        """
        Add multiple permissions to the preset.

        :param permissions: List of permissions to add. The permissions can be specified as either
            a list of permission objects, their codenames or their ids.
        :type permissions: List[Permission] | List[str] | List[int]
        """
        permissions = ModelsRegistry.get_permissions(permissions)

        for permission in permissions:
            self.add_permission(permission)

    @transaction.atomic
    def delete(self) -> None:
        """
        Delete the preset.
        """
        self.permissions.clear()
        super().delete()


class RolePresetUser(models.Model):
    """
    This model is used to give users access to private presets.
    """

    #: User given access to the preset.
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name=_("user"),
        related_name='User_role_presets'
    )
    #: Preset the user has been given access to.
    preset = models.ForeignKey(
        to=RolePreset,
        on_delete=models.CASCADE,
        verbose_name=_("preset"),
        related_name='role_preset_users'
    )

    def __str__(self) -> str:
        """
        Returns the string representation of the RolePresetUser object.

        :return: String representation of the preset and the user.
        :rtype: str
        """
        return f'{self.preset}_{self.user}'
