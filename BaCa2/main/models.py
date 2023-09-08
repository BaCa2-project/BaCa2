from typing import List

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.models import Group, Permission, ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from BaCa2.choices import PermissionTypes, DefaultCourseGroups
from course.manager import create_course as create_course_db, delete_course as delete_course_db


class UserManager(BaseUserManager):
    """
    This class manages the creation of new user objects. Its methods allow to create instances of default users and
    superusers with moderation privileges.
    The class extends BaseUserManager provided in django.contrib.auth and replaces the default UserManager model.
    """
    @staticmethod
    def _create_settings(self) -> 'Settings':
        """
        Create a new user settings object.

        :return: New user settings object.
        :rtype: Settings
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
        Create a new user using the provided information. This method is used by the create_user method and the
        create_superuser method.

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
        :param **other_fields: Values for non-required user fields.
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
            user_settings=self._create_settings(self),
            **other_fields
        )
        user.set_password(password)
        user.save(using='default')
        return user

    def create_user(self, email: str, username: str, password: str, **other_fields) -> 'User':
        """
        Create a new user without moderation privileges.

        :param email: New user's email.
        :type email: str
        :param username: New user's username.
        :type username: str
        :param password: New user's password.
        :type password: str
        :param **other_fields: Values for non-required user fields.
        """

        return self._create_user(email, username, password, False, False, **other_fields)

    def create_superuser(self, email: str, username: str, password: str, **other_fields) -> 'User':
        """
        Create a new user with all moderation privileges.

        :param email: New user's email.
        :type email: str
        :param username: New user's username.
        :type username: str
        :param password: New user's password.
        :type password: str
        :param **other_fields: Values for non-required user fields.
        """

        return self._create_user(email, username, password, True, True, **other_fields)


class CourseManager(models.Manager):
    def create_course(self, name: str, short_name: str = "") -> None:
        """
        Create a new course with given name and short name. If short name is not provided, it is automatically
        generated. A new database for the course is also created.

        :param name: Name of the new course.
        :type name: str
        :param short_name: Short name of the new course.
        :type short_name: str
        :return: The newly created course.
        :rtype: Course
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
        Delete the given course and its database.

        :param course: The course to delete.
        :type course: Course
        """
        delete_course_db(course.short_name)
        course.delete(using='default')

    @staticmethod
    def _generate_short_name(name: str) -> str:
        """
        Generate a short name for a course based on its name.

        :param name: Name of the course.
        :type name: str
        :return: Short name of the course.
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
    This class represents a course in the default database and contains a field pointing to the course's database.
    It allows for assigning users to course groups.
    """

    #: Name of the course.
    name = models.CharField(
        max_length=255
    )
    #: Short name of the course.
    short_name = models.CharField(
        max_length=31,
        unique=True
    )
    #: Name of the course's database. :py:class:`course.routing.InCourse` :py:mod:`course.models`
    db_name = models.CharField(
        max_length=127,
        unique=True
    )

    #: Indicates which class is used to manage Course objects.
    objects = CourseManager()

    def __str__(self):
        """
        Returns the name of this course's database.
        """
        return f"{self.db_name}"

    def add_user(self, user: 'User', group: Group):
        if not group:
            group = Group.objects.get(
                groupcourse__course=self,
                name=DefaultCourseGroups.VIEWER
            )

        if not group:
            raise ValidationError('No default viewer group exists for this course')

    def get_data(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'db_name': self.db_name
        }


class Settings(models.Model):
    """
    This model represents user settings. It is used to store user-specific settings in the database.
    """
    #: User's preferred UI theme.
    theme = models.CharField(
        _("UI theme"),
        max_length=255,
        default='dark'
    )


class User(AbstractBaseUser, PermissionsMixin):
    """
    This class stores user information. Its methods can be used to check permissions pertaining to the default database
    models as well as course access and models from course databases.
    The class extends AbstractBaseUser and PermissionsMixin classes provided in django.contrib.auth to replace the
    default User model.
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
    #: Indicates whether user has moderation privileges. Required by built-in Django authorisation system.
    is_staff = models.BooleanField(
        default=False
    )
    #: Indicates whether user has all available moderation privileges. Required by built-in Django authorisation system.
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

    #: Indicates which field should be considered as username. Required when replacing default Django User model.
    USERNAME_FIELD = 'username'
    #: Indicates which field should be considered as email. Required when replacing default Django User model.
    EMAIL_FIELD = 'email'
    #: Indicates which fields besides the USERNAME_FIELD are required when creating a User object.
    REQUIRED_FIELDS = ['email']

    #: Indicates which class is used to manage User objects.
    objects = UserManager()

    def __str__(self):
        return self.username

    @classmethod
    def exists(cls, user_id) -> bool:
        """
        Check whether a user with given id exists.

        :param user_id: The id of the user in question.
        :type user_id: BigInteger
        :return: True if the user exists.
        """

        return cls.objects.exists(pk=user_id)

    def can_access_course(self, course: Course) -> bool:
        """
        Check whether the user has been assigned to the given course through the UserCourse model.

        :param course: Course to check user access to.
        :type course: Course
        :return: True if user has been assigned to the given course.
        """

        if UserCourse.objects.filter(
                user=self,
                course=course
        ).exists():
            return True
        return False

    def check_general_permissions(
            self,
            model: models.Model,
            permissions: str or PermissionTypes or List[PermissionTypes] = 'all'
    ) -> bool:
        """
        Check permissions relating to default database models (non-course models).

        :param model: The model to check permissions for.
        :type model: models.Model
        :param permissions: Permissions to check for the given model. Permissions can be given as a PermissionTypes
            object/List of objects or as a string (in the format <app_label>.<permission_codename>) - the default
            option 'all' checks all permissions related to the model, both standard and custom. The 'all_standard'
            option checks the 'view', 'change', 'add' and 'delete' permissions for the given model.
        :type permissions: str or PermissionTypes or List[PermissionTypes] = 'all'
        :returns: True if user possesses given permissions for the given model.
        """

        if permissions == 'all':
            permissions = [f'{model._meta.app_label}.{p.codename}' for p in Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(model).id
            )]

        elif permissions == 'all_standard':
            permissions = [f'{model._meta.app_label}.{p.label}_{model._meta.model_name}' for p in PermissionTypes]

        elif isinstance(permissions, PermissionTypes):
            permissions = [f'{model._meta.app_label}.{permissions.label}_{model._meta.model_name}']

        elif isinstance(permissions, List):
            permissions = [f'{model._meta.app_label}.{p.label}_{model._meta.model_name}' for p in permissions]

        else:
            permissions = [permissions]

        for p in permissions:
            if not self.has_perm(p):
                return False
        return True

    def check_course_permissions(
            self,
            course: Course,
            model: models.Model,
            permissions: str or PermissionTypes or List[PermissionTypes] = 'all'
    ) -> bool:
        """
        Check permissions relating to course database models (checks whether the user has been assigned given
        model permissions within the scope of a particular course).

        :param course: The course to check the model permissions within.
        :type course: Course
        :param model: The model to check the permissions for.
        :type model: models.Model
        :param permissions: Permissions to check for the given model within the confines of the course. Permissions can
            be given as a PermissionTypes object/List of objects or 'all' - the default 'all' option checks all
            permissions related to the model.
        :returns: True if the user possesses given permissions for the given model within the scope of the course.
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
    This model is used to assign groups to courses.
    """

    #: Assigned group. :py:class:`django.contrib.auth.models.Group` :py:mod:`django.contrib.auth.models.`
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    #: Course the group is assigned to. :py:class:`Course`
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'groupcourse: {self.group.name} for {self.course}'


class UserCourse(models.Model):
    """
    Model used to assign users to courses with a given scope of course-specific permissions. This is achieved by
    assigning the given user to a GroupCourse object referencing the appropriate course and group with the appropriate
    permission set.
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
        return f'usercourse: {self.user} to {self.group_course}'
