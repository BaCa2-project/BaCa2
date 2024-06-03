import logging
from typing import Any, Dict

from django import forms
from django.utils.translation import gettext_lazy as _

from core.tools.mailer import TemplateMailer
from main.models import Announcement, User
from widgets.forms import BaCa2ModelForm, FormElementGroup, FormWidget
from widgets.forms.fields import (
    AlphanumericField,
    AlphanumericStringField,
    DateTimeField,
    ModelChoiceField
)

logger = logging.getLogger(__name__)


# ============================================ USER ============================================ #

# ----------------------------------------- create user ---------------------------------------- #

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
            post_target_url=UserModelView.post_url(),
            button_text=_('Add new user'),
            **kwargs
        )


# ------------------------------------ change personal data ------------------------------------ #

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
            post_target_url=UserModelView.post_url(),
            button_text=_('Save changes'),
            **kwargs
        )


# ======================================== ANNOUNCEMENT ======================================== #

# ------------------------------------- create announcement ------------------------------------ #

class CreateAnnouncementForm(BaCa2ModelForm):
    MODEL = Announcement
    ACTION = Announcement.BasicAction.ADD

    announcement_title = forms.CharField(
        label=_('Title'),
        required=True,
        min_length=1,
        max_length=Announcement._meta.get_field('title').max_length
    )
    announcement_content = forms.CharField(
        label=_('Text'),
        required=True,
        min_length=1,
        widget=forms.Textarea(attrs={'rows': 5})
    )
    announcement_custom_date = DateTimeField(label=_('Announcement date'), required=False)
    announcement_course = ModelChoiceField(
        label_format_string='[[name]]',
        help_text=_('Select course for which the announcement is intended. If you do not select '
                    'any course, the announcement will be visible to all users on the main page.'),
        required=False,
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        title = request.POST.get('announcement_title')
        content = request.POST.get('announcement_content')
        custom_date = request.POST.get('announcement_custom_date')
        course_id = request.POST.get('announcement_course', None)

        if not custom_date:
            custom_date = None

        Announcement.objects.create(title=title,
                                    content=content,
                                    custom_date=custom_date,
                                    course_id=course_id)
        message = _('Announcement') + ' ' + title + ' ' + _('created.')
        return {'message': message}


class CreateAnnouncementWidget(FormWidget):
    def __init__(self,
                 request,
                 form: CreateAnnouncementForm = None,
                 **kwargs) -> None:
        from main.views import AnnouncementModelView, CourseModelView

        if not form:
            form = CreateAnnouncementForm()

        form.fields['announcement_course'].data_source_url = CourseModelView.get_url()

        super().__init__(
            name='create_announcement_form_widget',
            request=request,
            form=form,
            post_target_url=AnnouncementModelView.post_url(),
            button_text=_('Create announcement'),
            element_groups=FormElementGroup(
                elements=['announcement_title', 'announcement_custom_date'],
                name='announcement_title_group',
                layout=FormElementGroup.Layout.HORIZONTAL
            ),
            **kwargs
        )


# -------------------------------------- edit announcement ------------------------------------- #

class EditAnnouncementForm(BaCa2ModelForm):
    MODEL = Announcement
    ACTION = Announcement.BasicAction.EDIT

    announcement_title = AlphanumericStringField(
        label=_('Title'),
        required=True,
        min_length=1,
        max_length=Announcement._meta.get_field('title').max_length
    )
    announcement_content = forms.CharField(
        label=_('Text'),
        required=True,
        widget=forms.Textarea(attrs={'rows': 5}),
        min_length=1
    )
    announcement_custom_date = DateTimeField(label=_('Announcement date'), required=False)
    announcement_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *,
                 announcement_id: int,
                 form_instance_id: int = 0,
                 request=None,
                 **kwargs):
        super().__init__(form_instance_id=form_instance_id, request=request, **kwargs)

        announcement = Announcement.objects.get(id=announcement_id)

        self.fields['announcement_title'].initial = announcement.title
        self.fields['announcement_content'].initial = announcement.content
        self.fields['announcement_custom_date'].initial = announcement.custom_date
        self.fields['announcement_id'].initial = announcement_id

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        announcement_id = request.POST.get('announcement_id')
        title = request.POST.get('announcement_title')
        content = request.POST.get('announcement_content')
        custom_date = request.POST.get('announcement_custom_date')

        if not custom_date:
            custom_date = None

        announcement = Announcement.objects.get(id=announcement_id)
        announcement.title = title
        announcement.content = content
        announcement.custom_date = custom_date
        announcement.save()

        message = _('Announcement') + ' ' + title + ' ' + _('successfully updated.')
        return {'message': message}


class EditAnnouncementFormWidget(FormWidget):
    def __init__(self,
                 request,
                 announcement_id: int,
                 form: EditAnnouncementForm = None,
                 **kwargs) -> None:
        from main.views import AnnouncementModelView

        if not form:
            form = EditAnnouncementForm(request=request, announcement_id=announcement_id)

        super().__init__(
            name='edit_announcement_form_widget',
            request=request,
            form=form,
            post_target_url=AnnouncementModelView.post_url(),
            button_text=_('Save changes'),
            reset_on_submit=False,
            element_groups=FormElementGroup(
                elements=['announcement_title', 'announcement_custom_date'],
                name='announcement_title_group',
                layout=FormElementGroup.Layout.HORIZONTAL
            ),
            **kwargs
        )


# ------------------------------------- delete announcement ------------------------------------ #

class DeleteAnnouncementForm(BaCa2ModelForm):
    MODEL = Announcement
    ACTION = Announcement.BasicAction.DEL

    announcement_id = forms.IntegerField(
        label=_('Announcement ID'),
        widget=forms.HiddenInput(attrs={'class': 'model-id', 'data-reset-on-refresh': 'true'}),
        required=True
    )

    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, Any]:
        announcement_id = request.POST.get('announcement_id')
        announcement = Announcement.objects.get(id=announcement_id)
        message = _('Announcement') + ' ' + announcement.title + ' ' + _('deleted.')
        announcement.delete()
        return {'message': message}
