from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class UserManager(BaseUserManager):

    def _create_user(self, email, username, password, is_staff, is_superuser, **other_fields):
        if not email:
            raise ValueError('Email address is required')

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


class Course(models.Model):
    name = models.CharField(
        max_length=255
    )
    short_name = models.CharField(
        max_length=31
    )


class GroupCourse(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )


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
