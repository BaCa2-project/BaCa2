from django import forms
from django.utils.translation import gettext_lazy as _

from main.models import Course
from widgets.forms.fields import AlphanumericStringField


class CourseName(AlphanumericStringField):
    """
    Form field for :class:`main.Course` name. Its validators check if the course name contains only
    the allowed characters, no double spaces and no trailing or leading spaces.
    """

    ACCEPTED_CHARS = [' ', '-', '+', '.', '/', '(', ')', ',', ':', '#']

    def __init__(self, **kwargs) -> None:
        super().__init__(
            min_length=5,
            max_length=Course._meta.get_field('name').max_length,
            **kwargs
        )

    @classmethod
    def syntax_validation_error_message(cls) -> str:
        """
        :return: Error message for syntax validation.
        :rtype: str
        """
        return _('Course name can only contain alphanumeric characters and the following special '
                 + 'characters: ') + ' '.join(cls.ACCEPTED_CHARS)


class CourseShortName(forms.CharField):
    """
    Form field for :class:`main.Course` short name. Its validators check if the course code is
    unique and if it contains only alphanumeric characters and underscores.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            label=_('Course code'),
            min_length=3,
            max_length=Course._meta.get_field('short_name').max_length,
            validators=[CourseShortName.validate_uniqueness, CourseShortName.validate_syntax],
            required=False,
            **kwargs
        )

    @staticmethod
    def validate_uniqueness(value: str) -> None:
        """
        Checks if the course short name is unique.

        :param value: Course short name.
        :type value: str

        :raises: ValidationError if the course short name is not unique.
        """
        if Course.objects.filter(short_name=value.lower()).exists():
            raise forms.ValidationError(_('Course with this code already exists.'))

    @staticmethod
    def validate_syntax(value: str) -> None:
        """
        Checks if the course short name contains only alphanumeric characters and underscores.

        :param value: Course short name.
        :type value: str

        :raises: ValidationError if the course short name contains characters other than
            alphanumeric characters and.
        """
        if any(not (c.isalnum() or c == '_') for c in value):
            raise forms.ValidationError(_('Course code can only contain alphanumeric characters and'
                                          'underscores.'))


class USOSCode(forms.CharField):
    """
    Form field for USOS subject and term codes of a course.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            min_length=1,
            validators=[USOSCode.validate_syntax],
            **kwargs
        )

    @staticmethod
    def validate_syntax(value: str) -> None:
        """
        Checks if the USOS code contains only alphanumeric characters, hyphens and dots.

        :param value: USOS code.
        :type value: str
        :raises: ValidationError if the USOS code contains characters other than alphanumeric
            characters, hyphens and dots.
        """
        if any(not c.isalnum() and c not in ['-', '+', '.', '/'] for c in value):
            raise forms.ValidationError(_('USOS code can only contain alphanumeric characters and '
                                          + 'the following special characters: - + . /'))
