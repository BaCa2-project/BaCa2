import logging
from typing import Any, Dict

from django import forms
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from core.tools.mailer import TemplateMailer
from main.models import User
from widgets.forms import BaCa2ModelForm, FormWidget
from widgets.forms.fields import AlphanumericField

logger = logging.getLogger(__name__)

token_generator = PasswordResetTokenGenerator()

class CreateUser(BaCa2ModelForm):
    MODEL = User
    ACTION = User.BasicAction.ADD

    email = forms.EmailField(required=True,
                             label=_('Email address'),
                             help_text=_('We will send an email with login and password to this '
                                         'address.'))
    first_name = forms.CharField(required=False, label=_('First name'))
    last_name = forms.CharField(required=False, label=_('Last name'))

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if User.objects.filter(email=email).exists():
            raise ValueError(_('User with this email already exists.'))

        user = User.objects.create_user(email=email,
                                        first_name=first_name,
                                        last_name=last_name,
                                        password=None)
        user.save()

        user_token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirm_url = f'http://{settings.HOST_NAME}/reset/{uid}/{user_token}/'
        try:
            mailer = TemplateMailer(mail_to=email,
                                    subject=_('Your new BaCa2 account'),
                                    template='new_account',
                                    context={'email': email,
                                             'first_name': user.first_name,
                                             'last_name': user.last_name,
                                             'confirm_url': confirm_url}, )
            mailer.send()
        except TemplateMailer.MailNotSent as e:
            logger.error(f'Failed to send email to {email}')
            user.delete()
            raise e

        return {'message': _('User created and email sent.')}


class CreateUserWidget(FormWidget):
    def __init__(self,
                 request,
                 form: CreateUser = None,
                 **kwargs) -> None:
        from main.views import UserModelView

        if not form:
            form = CreateUser()

        super().__init__(
            name='create_user_form_widget',
            request=request,
            form=form,
            post_target=UserModelView.post_url(),
            button_text=_('Add new user'),
            **kwargs
        )


# ------------------------------ Profile forms ------------------------------ #

class ChangePersonalData(BaCa2ModelForm):
    MODEL = User

    ACTION = User.BasicAction.EDIT
    nickname = AlphanumericField(
        min_length=3,
        max_length=20,
        required=False,
        label=_('Nickname'),
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        user = request.user
        nickname = request.POST.get('nickname')
        if not nickname:
            user.nickname = None
            user.save()
            return {'message': _('Personal data changed.')}
        if nickname == user.nickname:
            return {'message': _('No changes to apply.')}

        if nickname:
            nickname = nickname.strip()
        if len(nickname) > 20:
            raise ValueError(_('Nickname is too long.'))
        if len(nickname) < 3:
            raise ValueError(_('Nickname is too short.'))
        user.nickname = nickname

        user.save()
        return {'message': _('Personal data changed.')}


class ChangePersonalDataWidget(FormWidget):
    def __init__(self,
                 request,
                 form: ChangePersonalData = None,
                 **kwargs) -> None:
        from main.views import UserModelView

        if not form:
            form = ChangePersonalData()

        if request.user.nickname:
            form.fields['nickname'].initial = request.user.nickname

        super().__init__(
            name='change_personal_data_form_widget',
            request=request,
            form=form,
            post_target=UserModelView.post_url(),
            button_text=_('Save changes'),
            **kwargs
        )
