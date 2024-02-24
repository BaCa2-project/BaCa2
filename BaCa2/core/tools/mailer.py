import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


class Mailer(ABC):
    """
    Abstract base class for a mailer.

    :param mail_to: The recipient(s) of the email. Can be a string (for a single recipient) or an
        iterable of strings (for multiple recipients).
    :type mail_to: str | Iterable[str]
    :param subject: The subject of the email.
    :type subject: str
    :raises TypeError: If mail_to is not a string or an iterable of strings.
    """

    class MailNotSent(Exception):
        """Exception raised when an email fails to send."""
        pass

    def __init__(self,
                 mail_to: str | Iterable[str],
                 subject: str,
                 ignore_errors: bool = False):
        """
        Initialize the Mailer object.

        :param mail_to: The recipient(s) of the email.
        :type mail_to: str | Iterable[str]
        :param subject: The subject of the email.
        :type subject: str
        :param ignore_errors: If True, ignore errors when sending the email.
        :type ignore_errors: bool
        """
        if isinstance(mail_to, str):
            mail_to = [mail_to]
        self.mail_to = mail_to
        self.subject = subject
        self.ignore_errors = ignore_errors

    @abstractmethod
    def send(self) -> None:
        """
        Abstract method for sending an email.

        :raises NotImplementedError: Always (this method should be overridden by subclasses).
        """
        raise NotImplementedError('You must implement this method in your subclass.')


class TemplateMailer(Mailer):
    """
    Mailer that uses a Django template for the email content.

    :param mail_to: The recipient(s) of the email. Can be a string (for a single recipient) or an
        iterable of strings (for multiple recipients).
    :type mail_to: str | Iterable[str]
    :param subject: The subject of the email.
    :type subject: str
    :param template: The path to the Django template to use for the email content.
    :type template: str
    :param context: The context to render the template with.
    :type context: dict
    :raises TypeError: If mail_to is not a string or an iterable of strings.
    """

    #: The footer note to be added to the email.
    FOOTER_NOTE = _('Email sent automatically by BaCa2. Please do not reply.')

    def __init__(self,
                 mail_to: str | Iterable[str],
                 subject: str,
                 template: str,
                 ignore_errors: bool = False,
                 attachments: Dict[str, Path] = None,
                 context: Dict[str, Any] = None,
                 add_footer: bool = True):
        """
        Initialize the TemplateMailer object.

        :param mail_to: The recipient(s) of the email.
        :type mail_to: str | Iterable[str]
        :param subject: The subject of the email.
        :type subject: str
        :param template: The path to the Django template to use for the email content.
        :type template: str
        :param ignore_errors: If True, ignore errors when sending the email.
        :type ignore_errors: bool
        :param attachments: A dictionary of attachments to add to the email. The keys are the names
            of the attachments, and the values are the paths to the files.
        :type attachments: Dict[str, Path]
        :param context: The context to render the template with.
        :type context: Dict[str, Any]
        :param add_footer: If True, add a footer to the email.
        :type add_footer: bool
        """
        super().__init__(mail_to, subject, ignore_errors)
        self.template = f'mail/{template}'
        if context is None:
            context = {}
        self.context = context
        if attachments is None:
            attachments = {}
        self.attachments = attachments
        if add_footer:
            self.context['footer_note'] = self.FOOTER_NOTE

    @staticmethod
    def add_file(email: EmailMessage, file: Path, name: str) -> None:
        """
        Adds a file to the email as an attachment.

        :param email: The email to add the attachment to.
        :type email: EmailMessage
        :param file: The path to the file to attach.
        :type file: Path
        :param name: The name of the attachment.
        :type name: str
        """
        if not file.exists() or not file.is_file():
            raise FileNotFoundError(f'File {file} does not exist.')

        with open(file, 'rb') as f:
            email.attach(name + file.suffix, f.read(), mimetypes.guess_type(file)[0])

    def send(self) -> bool:
        """
        Sends an email using a Django template for the content.

        :raises MailNotSent: If the email fails to send.
        """
        try:
            template_loc = f'{self.template}_{settings.LANGUAGE_CODE}.html'
            html_content = render_to_string(template_loc, self.context)
        except TemplateDoesNotExist:
            template_loc = f'{self.template}.html'
            html_content = render_to_string(template_loc, self.context)

        email = EmailMultiAlternatives(
            subject=self.subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=self.mail_to
        )
        email.attach_alternative(html_content, 'text/html')
        email.content_subtype = 'html'

        for name, file in self.attachments.items():
            self.add_file(email, file, name)

        res = email.send(fail_silently=True)

        if res == 0 and not self.ignore_errors:
            raise self.MailNotSent('Email cannot be sent.')

        return res != 0
