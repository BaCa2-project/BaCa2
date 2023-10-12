from django import forms
from django.utils.translation import gettext_lazy as _

from base import BaCa2Form


class BaCa2RegisterForm(BaCa2Form):
    # TODO: rewrite
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
    # TODO: rewrite
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
