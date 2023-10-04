from django import forms

from main.models import User
from . import *


class UsernameField(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(
            label='Nazwa użytkownika',
            # min_length=User._meta.get_field('username').min_length,
            max_length=User._meta.get_field('username').max_length,
            required=kwargs.get('required', True),
            validators=[UsernameField.validate_uniqueness],
            **kwargs
        )

    @staticmethod
    def validate_uniqueness(value):
        if User.objects.filter(username=value).exists():
            raise forms.ValidationError('Nazwa użytkownika jest już zajęta.')


class BaCa2RegisterForm(BaCa2Form):
    username = UsernameField()

    email = forms.EmailField(
        label='Adres e-mail',
        required=True
    )
    password = forms.CharField(
        label='Hasło',
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )
    password_repeat = forms.CharField(
        label='Powtórz hasło',
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )

    def __init__(self, **kwargs):
        super().__init__(initial={'form_name': 'register_form'}, **kwargs)


class BaCa2RegisterWithUSOSForm(BaCa2Form):
    username = UsernameField()

    password = forms.CharField(
        label='Hasło',
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )
    password_repeat = forms.CharField(
        label='Powtórz hasło',
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )

    def __init__(self, **kwargs):
        super().__init__(initial={'form_name': 'register_form_usos'}, **kwargs)
