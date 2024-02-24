import logging
from typing import Any, Dict

from django import forms
from django.utils.translation import gettext_lazy as _

from core.tools.mailer import TemplateMailer
from main.models import User
from widgets.forms import BaCa2ModelForm, FormWidget

logger = logging.getLogger(__name__)


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

        password = User.objects.make_random_password(length=20)

        try:
            user = User.objects.get(email=email)
            if user:
                raise ValueError(_('User with this email already exists.'))
        except User.DoesNotExist:
            pass

        user = User.objects.create_user(email=email,
                                        first_name=first_name,
                                        last_name=last_name,
                                        password=password)
        user.save()

        try:
            mailer = TemplateMailer(mail_to=email,
                                    subject=_('Your new BaCa2 account'),
                                    template='new_account',
                                    context={'email': email, 'password': password}, )
            mailer.send()
        except TemplateMailer.MailNotSent as e:
            logger.error(f'Failed to send email to {email}')
            user.delete()
            raise e

        return {'success': _('User created and email sent.')}


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
