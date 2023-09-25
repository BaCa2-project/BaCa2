from typing import (List, Type, TypeVar)

from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin,
                                        BaseUserManager,
                                        Group,
                                        Permission,
                                        ContentType)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from BaCa2.choices import (PermissionTypes, DefaultCourseGroups)
from course.manager import (create_course as create_course_db, delete_course as delete_course_db)

model_cls = TypeVar("model_cls", bound=Type[models.Model])


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

    def create_course(self, name: str, short_name: str = "") -> None:
        """
        Create a new :py:class:`Course` with given name and short name. If short name is not
        provided,
        it is automatically generated. A new database for the course is also created.

        :param name: Name of the new course.
        :type name: str
        :param short_name: Short name of the new course.
        :type short_name: str
        """
        if short_name:
            short_name = short_name.lower()
            if Course.objects.filter(short_name=short_name).exists():
                raise ValidationError('A course with this short name already exists')
        else:
            short_name = self._generate_short_name(name)

        create_course_db(short_name)
        db_name = short_name + '_db'
        course = self.model(
            name=name,
            short_name=short_name,
            db_name=db_name
        )
        course.save(using='default')

    @staticmethod
    def delete_course(course: 'Course') -> None:
        """
        Delete given :py:class:`Course` and its database.

        :param course: The course to delete.
        :type course: Course
        """
        delete_course_db(course.short_name)
        course.delete(using='default')

    @staticmethod
    def _generate_short_name(name: str) -> str:
        """
        Generate a unique short name for a :py:class:`Course` based on its name.

        :param name: Name of the course.
        :type name: str

        :return: Short name for the course.
        :rtype: str
        """
        name_list = name.split()
        short_name = ""
        for word in name_list:
            short_name += word[0]

        now = timezone.now()
        short_name += str(now.year)

        if Course.objects.filter(short_name=short_name).exists():
            short_name += str(now.month)
        if Course.objects.filter(short_name=short_name).exists():
            short_name += str(now.day)
        if Course.objects.filter(short_name=short_name).exists():
            short_name += str(now.hour)
        if Course.objects.filter(short_name=short_name).exists():
            raise ValidationError('Could not generate a unique short name for the course')

        return short_name.lower()


class Course(models.Model):
    """
    This class represents a course in the default database. The short name of the course can be
    used to access the course's database with :py:class:`course.routing.InCourse`. The methods of
    this class deal with managing course database objects, as well as the users assigned to the
    course and their roles within it.
    """

    #: Name of the course.
    name = models.CharField(
        verbose_name=_("course name"),
        max_length=100
    )
    #: Short name of the course.
    # Used to access the course's database with :py:class:`course.routing.InCourse`.
    short_name = models.CharField(
        verbose_name=_("course short name"),
        max_length=20,
        unique=True
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

    def add_user(self, user: 'User', group: Group):
        if not group:
            group = Group.objects.get(
                groupcourse__course=self,
                name=DefaultCourseGroups.VIEWER
            )

        if not group:
            raise ValidationError('No default viewer group exists for this course')

        # TODO

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

        if UserCourse.objects.filter(user=self, course=course).exists():
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
                    groupcourse__usercourse__user=self
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
        on_delete=models.CASCADE
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


class UserCourse(models.Model):
    """
    This model is used to assign users to courses with a given scope of course-specific
    permissions. These permissions are defined by the role the user is assigned to within the
    course (represented by a :py:class:`GroupCourse` object).
    """

    #: Assigned user. :py:class:`User`
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    # Course the user is assigned to. :py:class:`Course`
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    # GroupCourse object representing the course group user is assigned to. :py:class:`GroupCourse`
    group_course = models.ForeignKey(
        GroupCourse,
        on_delete=models.CASCADE
    )

    def __str__(self):
        """
        Returns the string representation of the UserCourse object.

        :return: :py:meth:`User.__str__` representation of the user and the
            :py:meth:`GroupCourse.__str__` representation of the group course.
        :rtype: str
        """
        return f'.{self.user}.{self.group_course}'
