from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
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
