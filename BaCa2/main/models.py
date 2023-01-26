from typing import List

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.models import Group, Permission, ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from BaCa2.choices import PermissionTypes, DefaultCourseGroups


class UserManager(BaseUserManager):

    def _create_user(self, email, username, password, is_staff, is_superuser, **other_fields):
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
            **other_fields
        )
        user.set_password(password)
        user.save(using='default')
        return user

    def create_user(self, email, username, password, **other_fields):
        return self._create_user(email, username, password, False, False, **other_fields)

    def create_superuser(self, email, username, password, **other_fields):
        return self._create_user(email, username, password, True, True, **other_fields)


class Course(models.Model):
    name = models.CharField(
        max_length=255
    )
    short_name = models.CharField(
        max_length=31
    )
    db_name = models.CharField(
        max_length=127,
        default='default'
    )

    def __str__(self):
        return f"{self.db_name}"

    def add_user(self, user: 'User', group: Group):
        if not group:
            group = Group.objects.get(
                groupcourse__course=self,
                name=DefaultCourseGroups.VIEWER
            )

        if not group:
            raise ValidationError('No default viewer group exists for this course')




class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        _("email address"),
        max_length=255,
        unique=True
    )
    username = models.CharField(
        _("username"),
        max_length=255,
        unique=True
    )
    is_staff = models.BooleanField(
        default=False
    )
    is_superuser = models.BooleanField(
        default=False
    )
    first_name = models.CharField(
        _("first name"),
        max_length=255,
        blank=True
    )
    last_name = models.CharField(
        _("last name"),
        max_length=255,
        blank=True
    )
    date_joined = models.DateField(
        auto_now_add=True
    )

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username

    @classmethod
    def exists(cls, user_id):
        return cls.objects.exists(pk=user_id)

    def can_access_course(
            self,
            course: Course
    ):
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
    ):
        """
        Check permissions relating to default database models (non-course models).

        :param model: The model to check permissions for.
        :type model: models.Model
        :param permissions: Permissions to check for the given model. Permissions can be given as a PermissionTypes
        object/List of objects or as a string (in the format [app_label].[permission_codename]) - the default option
        'all' checks all permissions related to the model, both standard and custom. The 'all_standard' option checks
        the 'view', 'change', 'add' and 'delete' permissions for the given model.
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
            permissions: 'all' or PermissionTypes or List[PermissionTypes] = 'all'
    ):
        """
        Check permissions relating to course database models (checks whether the user has been assigned given
        model permissions within the scope of a particular course).

        :param course: The course to check the model permissions within.
        :type course: Course
        :param model: The model to check the permissions for.
        :type model: models.Model
        :param permissions: Permissions to check for the given model within the confines of the course. Permissions can
        be given as a PermissionTypes object/List of objects or 'all' - the default 'all' option checks all permissions
        related to the model.
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
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'groupcourse: {self.group.name} for {self.course}'


class UserCourse(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    group_course = models.ForeignKey(
        GroupCourse,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'usercourse: {self.user} to {self.group_course}'
