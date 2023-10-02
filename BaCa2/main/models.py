from typing import (List, Type, Union)

from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin,
                                        BaseUserManager,
                                        Group,
                                        Permission,
                                        ContentType)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from BaCa2.choices import PermissionTypes
from course.manager import (create_course as create_course_db, delete_course as delete_course_db)
from util.models import (model_cls,
                         get_all_permissions_for_model,
                         get_all_models_from_app,
                         get_model_permission_by_label,
                         delete_populated_group,
                         replace_special_symbols)


class UserManager(BaseUserManager):
    """
    This class manages the creation of new :py:class:`User` objects. Its methods allow for creation
    of default and superuser user instances.

    This class extends the BaseUserManager provided in  :py:mod:`django.contrib.auth` and replaces
    the default UserManager class.
    """

    @staticmethod
    def _create_settings() -> 'Settings':
        """
        Create a new user :py:class:`Settings` object.

        :return: New user settings object.
        :rtype: :py:class:`Settings`
        """

        settings = Settings()
        settings.save(using='default')
        return settings

    def _create_user(
            self,
            email: str,
            username: str,
            password: str,
            is_staff: bool,
            is_superuser: bool,
            **other_fields
    ) -> 'User':
        """
        Create a new :py:class:`User` object along with its :py:class:`Settings` object. This
        private method is used by the :py:meth:`create_user` and :py:meth:`create_superuser`
        manager methods.

        :param email: New user's email.
        :type email: str
        :param username: New user's username.
        :type username: str
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

        if not email:
            raise ValidationError('Email address is required')
        if not username:
            raise ValidationError('Username is required')
        if not password:
            raise ValidationError('Password is required')

        now = timezone.now()
        _email = self.normalize_email(email)
        user = self.model(
            email=_email,
            username=username,
            is_staff=is_staff,
            is_superuser=is_superuser,
            date_joined=now,
            user_settings=self._create_settings(),
            **other_fields
        )
        user.set_password(password)
        user.save(using='default')
        return user

    def create_user(self, email: str, username: str, password: str, **other_fields) -> 'User':
        """
        Create a new :py:class:`User` without moderation privileges.

        :param email: New user's email.
        :type email: str
        :param username: New user's username.
        :type username: str
        :param password: New user's password.
        :type password: str
        :param other_fields: Values for non-required user fields.

        :return: The newly created user.
        :rtype: :py:class:`User`
        """

        return self._create_user(email=email,
                                 username=username,
                                 password=password,
                                 is_staff=False,
                                 is_superuser=False,
                                 **other_fields)

    def create_superuser(self, email: str, username: str, password: str, **other_fields) -> 'User':
        """
        Create a new :py:class:`User` with all moderation privileges.

        :param email: New user's email.
        :type email: str
        :param username: New user's username.
        :type username: str
        :param password: New user's password.
        :type password: str
        :param other_fields: Values for non-required user fields.

        :return: The newly created superuser.
        :rtype: :py:class:`User`
        """

        return self._create_user(email=email,
                                 username=username,
                                 password=password,
                                 is_staff=True,
                                 is_superuser=True,
                                 **other_fields)


class CourseManager(models.Manager):
    """
    This class manages the creation and deletion of :py:class:`Course` objects. It calls on
    :py:mod:`course.manager` methods to create and delete course databases along with corresponding
    course objects in the 'default' database.
    """

    def create_course(self,
                      name: str,
                      short_name: str = "",
                      usos_course_code: str | None = None,
                      usos_term_code: str | None = None,
                      roles: List[Group] | None = None,
                      default_role: Group | int | str | None = None,
                      create_basic_roles: bool = False) -> 'Course':
        """
        Create a new :py:class:`Course` with given name, short name, USOS code and roles.
        A new database for the course is also created which can be accessed using the course's
        short name with :py:class:`course.routing.InCourse`.

        :param name: Name of the new course.
        :type name: str
        :param short_name: Short name of the new course. If no short name is provided, a unique
            short name is generated based on the course name or USOS code (if it's provided). The
            short name cannot contain the '|' character.
        :type short_name: str
        :param usos_course_code: Subject code of the course in the USOS system.
        :type usos_course_code: str
        :param usos_term_code: Term code of the course in the USOS system.
        :type usos_term_code: str
        :param roles: List of groups to assign to the course. These groups represent the roles
            users can be assigned to within the course. If no roles are provided, a basic set of
            roles is created for the course. In addition, a course will always receive an admin
            role with all permissions assigned.
        :type roles: List[Group]
        :param default_role: The default role assigned to users within the course, if no other role
            is specified. If no default role is provided, the first role from the list of roles will
            be used - in case of basic roles creation, this role will be 'students'. The default
            role can be specified as either the group object, its id or its name.
        :type default_role: Group
        :param create_basic_roles: Indicates whether a basic set of roles should be created for the
            course regardless of whether any roles are provided.
        :type create_basic_roles: bool

        :return: The newly created course.
        :rtype: Course
        """
        if (usos_course_code is not None) ^ (usos_term_code is not None):
            raise ValidationError('Both USOS course code and USOS term code must be provided or neither')

        if short_name:
            short_name = short_name.lower()
        else:
            short_name = self._generate_short_name(name, usos_course_code, usos_term_code)
        self.validate_short_name(short_name)

        roles = self._create_course_roles(short_name=short_name,
                                          roles=roles,
                                          default_role=default_role,
                                          create_basic_roles=create_basic_roles)

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

        for role in roles:
            course.add_role(role)

        return course

    @staticmethod
    def delete_course(course: 'Course') -> None:
        """
        Delete given :py:class:`Course` and its database. In addition, all groups assigned to the
        course are deleted.

        :param course: The course to delete.
        :type course: Course
        """
        roles = list(course.roles())
        delete_course_db(course.short_name)
        course.delete(using='default')
        for role in roles:
            delete_populated_group(role)

    @staticmethod
    def validate_short_name(short_name: str) -> None:
        """
        Validate a given short name. A short name is valid if it consists only of alphanumeric
        characters and underscores. It also has to be unique.

        :param short_name: Short name to validate.
        :type short_name: str

        :raises ValidationError: If the short name is invalid.
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
        """
        if usos_course_code and usos_term_code:
            short_name = f'{replace_special_symbols(usos_course_code, "_")}_'\
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
                short_name += f'_{len(Course.objects.filter(short_name__startswith=short_name)) + 1}'

        if Course.objects.filter(short_name=short_name).exists():
            raise ValidationError('Could not generate a unique short name for the course')

        return short_name

    @staticmethod
    def _create_course_roles(short_name: str,
                             roles: List[Group] | None = None,
                             default_role: Group | int | str | None = None,
                             create_basic_roles: bool = False) -> List[Group]:
        """
        Create and validate a set of roles for a course based on roles provided - or if no roles
        are provided - on a default set of roles. The resulting list of roles has the default role
        for the course as its first element and the admin role as its last.

        :param short_name: Short name of the course. Used to create role names.
        :type short_name: str
        :param roles: List of groups to assign to the course. These groups represent the roles
            users can be assigned to within the course. If no roles are provided, a default set of
            roles is created for the course. In addition, a course will always receive an admin
            role with all permissions assigned.
        :type roles: List[Group]
        :param default_role: The default role assigned to users within the course, if no other role
            is specified. If no default role is provided, the first role from the list of roles will
            be used - in case of basic roles creation, this role will be 'students'. The default
            role can be specified as either the group object, its id or its verbose name.
        :type default_role: Group
        :param create_basic_roles: Indicates whether a basic set of roles should be created for the
            course regardless of whether any roles are provided.
        :type create_basic_roles: bool

        :return: List of roles for the course. The default role for the course is the first element
            of the list and the admin role is the last.
        :rtype: List[Group]
        """
        if default_role and not roles:
            raise Course.CourseRoleError("Default role provided without any course roles")

        if not roles:
            roles = CourseManager._create_basic_course_roles(short_name)
        elif create_basic_roles:
            roles = CourseManager._create_basic_course_roles(short_name) + roles
        roles.append(CourseManager._create_course_admin_role(short_name))

        for role in roles:
            if role.name.split('|')[0] != short_name:
                raise Course.CourseRoleError("Role name does not match course short name")
            if role.groupcourse_set.exists():
                raise Course.CourseRoleError("Role already assigned to a different \
                                                    course")

        if isinstance(default_role, int):
            default_role = Group.objects.get(id=default_role)
            if default_role not in roles:
                raise Course.CourseRoleError("Default role with given id not in course \
                                                    roles.")
        elif isinstance(default_role, str):
            default_role = [g for g in roles if Course.get_role_verbose_name(g) == default_role]
            if not default_role:
                raise Course.CourseRoleError("Default role with given name not in course \
                                                    roles.")
            default_role = default_role[0]
        elif default_role:
            if default_role not in roles:
                raise Course.CourseRoleError("Default role not in course roles.")

        if default_role:
            roles.insert(0, roles.pop(roles.index(default_role)))

        return roles

    @staticmethod
    def _create_basic_course_roles(short_name: str) -> List[Group]:
        """
        Create a basic set of roles for a course. Used when no roles are provided during course
        creation. Or when roles are provided, but the option to create basic roles is set.
        Default roles consist of 'students' and 'staff' groups with the following permissions:
        'students' and 'staff' - 'view' permission for all course models, 'add' permission for
        the 'Submit' model; 'staff' - 'add', 'change' and 'delete' permissions for the 'Round',
        'Task', 'TestSet' and 'Test' models.

        :param short_name: Short name of the course. Used to create role names.
        :type short_name: str

        :return: List of default course roles.
        :rtype: List[Group]
        """
        course_models = get_all_models_from_app('course')
        students = Group.objects.create(
            name=_(Course.create_role_name('students', short_name))
        )
        staff = Group.objects.create(
            name=_(Course.create_role_name('staff', short_name))
        )
        roles = [students, staff]

        for model in course_models.values():
            for role in roles:
                role.permissions.add(
                    get_model_permission_by_label(model, PermissionTypes.VIEW.label).id
                )

        for role in roles:
            role.permissions.add(
                get_model_permission_by_label(course_models['Submit'], PermissionTypes.ADD.label).id
            )

        for model in [course_models[i] for i in ['Round', 'Task', 'TestSet', 'Test']]:
            staff.permissions.add(
                get_model_permission_by_label(model, PermissionTypes.ADD.label).id
            )
            staff.permissions.add(
                get_model_permission_by_label(model, PermissionTypes.EDIT.label).id
            )
            staff.permissions.add(
                get_model_permission_by_label(model, PermissionTypes.DEL.label).id
            )

        return roles

    @staticmethod
    def _create_course_admin_role(short_name: str) -> Group:
        """
        Create an 'admin' role for a course. The role has all permissions related to all course
        models assigned to it.

        :param short_name: Short name of the course. Used to create the role name.
        :type short_name: str

        :return: The 'admin' role.
        :rtype: Group
        """
        course_models = get_all_models_from_app('course')
        admin_role = Group.objects.create(
            name=_(Course.create_role_name('admin', short_name))
        )

        for model in course_models.values():
            for perm_id in [perm.id for perm in get_all_permissions_for_model(model)]:
                admin_role.permissions.add(perm_id)

        return admin_role


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

    #: Name of the course.
    name = models.CharField(
        verbose_name=_("course name"),
        max_length=100,
        blank=False
    )
    #: Short name of the course.
    # Used to access the course's database with :py:class:`course.routing.InCourse`.
    short_name = models.CharField(
        verbose_name=_("course short name"),
        max_length=20,
        unique=True,
        blank=False
    )
    #: Subject code of the course in the USOS system.
    # Used for automatic assignment of USOS registered users to the course
    USOS_course_code = models.CharField(
        verbose_name=_("Subject code"),
        max_length=20,
        blank=True,
        null=True
    )
    #: Term code of the course in the USOS system.
    # Used for automatic assignment of USOS registered users to the course
    USOS_term_code = models.CharField(
        verbose_name=_("Term code"),
        max_length=20,
        blank=True,
        null=True
    )
    #: The default role assigned to users within the course, if no other role is specified.
    default_role = models.ForeignKey(
        verbose_name=_("default role"),
        to=Group,
        on_delete=models.PROTECT,
        limit_choices_to={'groupcourse__course': None},
        null=False,
        blank=False,
        related_name='+'
    )
    #: The admin role for the course. The role has all permissions related to all course models.
    # This group is automatically created during course creation.
    admin_role = models.ForeignKey(
        verbose_name=_("admin role"),
        to=Group,
        on_delete=models.PROTECT,
        limit_choices_to={'groupcourse__course': None},
        null=False,
        blank=False,
        related_name='+'
    )

    #: Manager class for the Course model.
    objects = CourseManager()

    def __str__(self) -> str:
        """
        Returns the string representation of the Course object.

        :return: Short name and name of the course.
        :rtype: str
        """
        return f"{self.short_name}.{self.name}"

    def user_is_member(self, user: 'User') -> bool:
        """
        Check whether a given user is a member of the course.

        :param user: The user to check.
        :type user: User

        :return: `True` if the user is a member of the course, `False` otherwise.
        :rtype: bool
        """
        return Group.objects.filter(user=user, groupcourse__course=self).exists()

    def roles(self) -> Union[QuerySet, List[Group]]:
        """
        Returns a QuerySet of groups assigned to the course. These groups represent the roles
        users can be assigned to within the course.

        :return: QuerySet of groups assigned to the course.
        :rtype: QuerySet[Group]
        """
        return Group.objects.filter(groupcourse__course=self)

    def get_role(self, verbose_name: str) -> Group:
        """
        Returns the role with given verbose name assigned to the course.

        :param verbose_name: Verbose name of the role to return.
        :type verbose_name: str

        :return: The role with given name assigned to the course.
        :rtype: Group
        """
        role_name = Course.create_role_name(verbose_name, self.short_name)
        return Group.objects.get(groupcourse__course=self, name=role_name)

    def role_exists(self, verbose_name: str) -> bool:
        """
        Check whether a role with given verbose name exists within the course.

        :param verbose_name: Verbose name of the role to check.
        :type verbose_name: str

        :return: `True` if the role exists, `False` otherwise.
        :rtype: bool
        """
        role_name = Course.create_role_name(verbose_name, self.short_name)
        return Group.objects.filter(groupcourse__course=self, name=role_name).exists()

    @staticmethod
    def get_role_verbose_name(role: Group | str):
        """
        Returns the verbose name of a given role or extracts it from the role's name.

        :param role: The role to return the verbose name for or the role's name.
        :type role: Group | str

        :return: The verbose name of the role.
        :rtype: str
        """
        if isinstance(role, Group):
            role = role.name
        return role.split('|')[1]

    @staticmethod
    def create_role_name(verbose_name: str, short_name: str) -> str:
        """
        Create a unique role name based on a given verbose name and course short name. Role names
        have the following format: `short_name` + '|' + `verbose_name`. This is done to ensure that
        role names are unique across all courses while many courses can have roles with the same
        verbose name.

        :param verbose_name: Verbose name of the role.
        :type verbose_name: str
        :param short_name: Short name of the course.
        :type short_name: str

        :return: Unique role name.
        :rtype: str
        """
        return f"{short_name}|{verbose_name}"

    def get_role_permissions(self, role_verbose_name: str) -> Union[QuerySet, List[Permission]]:
        """
        Returns the permissions assigned to the role with given verbose name within the course.

        :param role_verbose_name: Verbose name of the role to return permissions for.
        :type role_verbose_name: str

        :return: QuerySet of permissions assigned to the role.
        :rtype: QuerySet[Permission]
        """
        return self.get_role(role_verbose_name).permissions.all()

    def get_users(self, role: Group | str | None = None) -> Union[QuerySet, List['User']]:
        """
        Returns the users assigned to the course. If a role is specified, only users assigned to
        the given role are returned.

        :param role: The role to return users for. If no role is specified, all users assigned to
            the course are returned. The role can be specified as either the group object or its
            name.
        :type role: Group | str

        :return: QuerySet of users assigned to the course with given role. If no role specified,
            the QuerySet contains all users assigned to the course.
        :rtype: QuerySet[User]
        """
        users = User.objects.filter(groups__groupcourse__course=self)

        if not role:
            return users
        if isinstance(role, str):
            role = self.get_role(role)

        return users.filter(groups=role)

    def get_users_with_permission(self, permission: Permission) -> Union[QuerySet, List['User']]:
        """
        Returns all users assigned to the course who belong to a role with given permission.

        :param permission: The permission to check for.
        :type permission: Permission

        :return: QuerySet of users assigned to the course with given permission.
        :rtype: QuerySet[User]
        """
        roles = Group.objects.filter(groupcourse__course=self, permissions=permission)
        return User.objects.filter(groups__in=roles)

    def add_user(self, user: 'User', role: Group | str | None = None) -> None:
        """
        Assign given user to the course with given role. If no role is specified, the user is
        assigned to the course with the default role.

        :param user: The user to be assigned.
        :type user: User
        :param role: The role to assign the user to. If no role is specified, the user is assigned
            to the course with the default role. The role can be specified as either the group
            object or its verbose name.
        :type role: Group | str
        """
        if not role:
            role = self.default_role
        elif isinstance(role, str):
            role = self.get_role(role)

        role.user_set.add(user)

    def _validate_new_role(self, role: Group):
        """
        Check whether a given role can be assigned to the course. Raises an exception if the role
        cannot be assigned.

        :param role: The role to be validated.
        :type role: Group

        :raises Course.CourseRoleError: If the role name does not match the course short name or
            the role is already assigned to a different course.
        """
        if role.name.split('|')[0] != self.short_name:
            raise Course.CourseRoleError("Role name does not match course short name")
        if GroupCourse.objects.filter(group=role, course=self).exists():
            raise Course.CourseRoleError("Group already assigned to a different course")

    def add_role(self, role: Group) -> None:
        """
        Add a new role to the course if it passes validation.

        :param role: The role to add.
        :type role: Group
        """
        self._validate_new_role(role)
        GroupCourse.objects.create(group=role, course=self)

    def remove_role(self, role: Group) -> None:
        """
        Remove a role from the course and delete it. Cannot be used to remove the default role, the
        admin role or a role with users assigned to it.

        :param role: The role to remove.
        :type role: Group

        :raises Course.CourseRoleError: If the role is the default role, the admin role or has
            users assigned to it.
        """
        if role == self.default_role:
            raise Course.CourseRoleError("Default role cannot be removed from the course")
        if role == self.admin_role:
            raise Course.CourseRoleError("Admin role cannot be removed from the course")
        if role.user_set.exists():
            raise Course.CourseRoleError("Cannot remove a role with users assigned to it")

        delete_populated_group(role)

    def change_user_role(self, user: 'User', new_role: Group | str) -> None:
        """
        Change the role of a given user within the course.

        :param user: The user whose role is to be changed.
        :type user: User
        :param new_role: The role to assign to the user. The role can be specified as either the
            group object or its name.
        :type new_role: Group | str
        """
        if not self.user_is_member(user):
            raise Course.CourseMemberError("Change of role was attempted for a user who is not a \
                                           member of the course")

        if isinstance(new_role, str):
            new_role = self.get_role(new_role)

        Group.objects.get(groupcourse__course=self, user=user).delete()
        new_role.user_set.add(user)

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
            'USOS_code': self.USOS_code,
        }


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


class User(AbstractBaseUser, PermissionsMixin):
    """
    This class stores user information. Its methods can be used to check permissions pertaining to
    the default database models as well as course access and models from course databases.
    The class extends AbstractBaseUser and PermissionsMixin classes provided in django.contrib.auth
    to replace the default User model.
    """

    #: User's email. Can be used to log in.
    email = models.EmailField(
        _("email address"),
        max_length=255,
        unique=True
    )
    #: Unique username. Can be used during login instead of email.
    username = models.CharField(
        _("username"),
        max_length=255,
        unique=True
    )
    #: Indicates whether user has moderation privileges.
    # Required by built-in Django authorisation system.
    is_staff = models.BooleanField(
        default=False
    )
    #: Indicates whether user has all available moderation privileges.
    # Required by built-in Django authorisation system.
    is_superuser = models.BooleanField(
        default=False
    )
    #: User's first name.
    first_name = models.CharField(
        _("first name"),
        max_length=255,
        blank=True
    )
    #: User's last name.
    last_name = models.CharField(
        _("last name"),
        max_length=255,
        blank=True
    )
    #: Date of account creation.
    date_joined = models.DateField(
        auto_now_add=True
    )
    #: User's settings.
    user_settings = models.OneToOneField(
        Settings,
        on_delete=models.CASCADE
    )

    #: Indicates which field should be considered as username.
    # Required when replacing default Django User model.
    USERNAME_FIELD = 'username'

    #: Indicates which field should be considered as email.
    # Required when replacing default Django User model.
    EMAIL_FIELD = 'email'

    #: Indicates which fields besides the USERNAME_FIELD are required when creating a User object.
    REQUIRED_FIELDS = ['email']

    #: Manager class for the User model.
    objects = UserManager()

    def __str__(self) -> str:
        """
        Returns the string representation of the User object.

        :return: User's username.
        :rtype: str
        """
        return self.username

    @classmethod
    def exists(cls, user_id) -> bool:
        """
        Check whether a user with given id exists.

        :param user_id: The id of the user in question.
        :type user_id: BigInteger

        :return: `True` if user with given id exists, `False` otherwise.
        :rtype: bool
        """

        return cls.objects.exists(pk=user_id)

    def can_access_course(self, course: Course) -> bool:
        """
        Check whether the user has been assigned to a given course.

        :param course: Course to check user's access to.
        :type course: Course

        :return: `True` if user has been assigned to the course, `False` otherwise.
        :rtype: bool
        """
        if Group.objects.filter(user=self, groupcourse__course=course).exists():
            return True
        return False

    def check_general_permissions(
            self,
            model: model_cls,
            permissions: str or PermissionTypes or List[PermissionTypes] = 'all'
    ) -> bool:
        """
        Check whether a user possesses a specified permission/list of permissions for a given
        'default' database model. The method checks both user-specific permissions and group-level
        permissions.

        :param model: The model to check permissions for.
        :type model: Type[models.Model]
        :param permissions: Permissions to check for the given model. Permissions can be given as a
            PermissionTypes object/List of objects or as a string (in the format
            <app_label>.<permission_codename>) - the default option 'all' checks all permissions
            related to the model, both standard and custom. The 'all_standard' option checks the
            'view', 'change', 'add' and 'delete' permissions for the given model.
        :type permissions: str or PermissionTypes or List[PermissionTypes]

        :returns: `True` if the user possesses the specified permission/s for the given model,
            `False` otherwise.
        :rtype: bool
        """

        if permissions == 'all':
            permissions = [f'{model._meta.app_label}.{p.codename}' for p in
                           Permission.objects.filter(
                               content_type=ContentType.objects.get_for_model(model).id
                           )]

        elif permissions == 'all_standard':
            permissions = [f'{model._meta.app_label}.{p.label}_{model._meta.model_name}' for p in
                           PermissionTypes]

        elif isinstance(permissions, PermissionTypes):
            permissions = [f'{model._meta.app_label}.{permissions.label}_{model._meta.model_name}']

        elif isinstance(permissions, List):
            permissions = [f'{model._meta.app_label}.{p.label}_{model._meta.model_name}' for p in
                           permissions]

        else:
            permissions = [permissions]

        for p in permissions:
            if not self.has_perm(p):
                return False
        return True

    def check_course_permissions(
            self,
            course: Course,
            model: model_cls,
            permissions: str or PermissionTypes or List[PermissionTypes] = 'all'
    ) -> bool:
        """
        Check whether a user possesses a specified permission/list of permissions for a given
        model within the scope of a particular course. The method checks only group-level
        permissions (user-specific permissions cannot be used to assign permissions within the
        scope of a course).

        :param course: The course to check the model permissions within.
        :type course: :class:`Course`
        :param model: The model to check the permissions for.
        :type model: Type[models.Model]
        :param permissions: Permissions to check for the given model within the confines of the
            course. Permissions can be given as a PermissionTypes object/List of objects or 'all' -
            the default 'all' option checks all permissions related to the model.
        :type permissions: str or PermissionTypes or List[PermissionTypes]

        :returns: `True` if the user possesses the specified permission/s for the given model
            within the scope of the course, `False` otherwise.
        :rtype: bool
        """

        if not self.can_access_course(course):
            return False

        if permissions == 'all':
            permissions = PermissionTypes

        if isinstance(permissions, PermissionTypes):
            permissions = [permissions]

        for permission in permissions:
            if not Group.objects.filter(
                    permissions__codename=f'{permission.label}_{model._meta.model_name}',
                    groupcourse__course=course,
                    user=self
            ).exists():
                return False
        return True


class GroupCourse(models.Model):
    """
    This model is used to assign groups to courses. Groups assigned to a course represent the roles
    (and the corresponding sets of permissions) users can have within the course.
    """

    #: Assigned group. :py:class:`django.contrib.auth.models.Group`
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        limit_choices_to={'groupcourse': None}
    )
    #: :py:class:`Course` the group is assigned to.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        """
        Returns the string representation of the GroupCourse object.

        :return: Name of the group and :py:meth:`Course.__str__` representation of the course.
        :rtype: str
        """
        return f'{self.group.name}.{self.course}'
