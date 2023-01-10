from typing import List

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from BaCa2.choices import PermissionTypes


class UserManager(BaseUserManager):

    def _create_user(self, email, username, password, is_staff, is_superuser, **other_fields):
        if not email:
            raise ValidationError('Email address is required')

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

    def can_access_course(self, course: Course):
        if UserCourse.objects.filter(course=course, user=self).exists():
            return True
        return False

    def check_general_permissions(
            self,
            model: models.Model,
            permissions: str or PermissionTypes or List[PermissionTypes] = 'all'
    ):
        if permissions == 'all':
            permissions = Permission.objects.filter(
                content_type__model=model
            )
        elif isinstance(permissions, str):
            permissions = Permission.objects.filter(
                codename=permissions
            )

        if isinstance(permissions, PermissionTypes):
            permissions = Permission.objects.filter(
                codename=f'{permissions.label}_{model._meta.model_name}'
            )

        if isinstance(permissions, List):
            codenames = []
            for p in permissions:
                codenames.append(f'{p.label}_{model._meta.model_name}')

            permissions = Permission.objects.filter(
                codename__in=codenames
            )

        for permission in permissions:
            if not Group.objects.filter(
                permissions=permission,
                user_set=self
            ).exists():
                return False
        return True

    def check_course_permissions(
            self,
            course: Course,
            model: models.Model,
            permissions: 'all' or PermissionTypes or List[PermissionTypes] = 'all'
    ):
        if not self.can_access_course(course):
            return False

        if permissions == 'all':
            permissions = PermissionTypes[:]

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
