from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskJudgingMode(models.TextChoices):
    LIN = 'LIN', _('Linear')
    UNA = 'UNA', _('Unanimous')


class ResultStatus(models.TextChoices):
    PND = 'PND', _('Pending')
    OK = 'OK', _('Test accepted')
    ANS = 'ANS', _('Wrong answer')
    RTE = 'RTE', _('Runtime error')
    MEM = 'MEM', _('Memory exceeded')
    TLE = 'TLE', _('Time limit exceeded')
    CME = 'CME', _('Compilation error')
    EXT = 'EXT', _('Unknown extension')
    INT = 'INT', _('Internal error')


class PermissionCheck(models.TextChoices):
    INDV = 'individual', _('Individual Permissions')
    GRP = 'group', _('Group-level Permissions')
    GEN = 'general', _('All Permissions')


class ModelAction(models.TextChoices):
    pass


class BasicModelAction(ModelAction):
    ADD = 'ADD', 'add'
    DEL = 'DEL', 'delete'
    EDIT = 'EDIT', 'change'
    VIEW = 'VIEW', 'view'


class TaskDescriptionExtension(models.TextChoices):
    PDF = 'PDF', _('PDF')
    MD = 'MD', _('Markdown')
    HTML = 'HTML', _('HTML')
    TXT = 'TXT', _('Plain text')
