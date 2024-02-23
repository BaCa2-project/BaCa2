from typing import Self

from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskJudgingMode(models.TextChoices):
    UNA = 'UNA', _('Unanimous')
    LIN = 'LIN', _('Linear')


class ResultStatus(models.TextChoices):
    PND = 'PND', _('Pending')
    OK = 'OK', _('Accepted')
    ANS = 'ANS', _('Wrong answer')
    TLE = 'TLE', _('Time limit exceeded')
    RTE = 'RTE', _('Runtime error')
    MEM = 'MEM', _('Memory exceeded')
    CME = 'CME', _('Compilation error')
    EXT = 'EXT', _('Unknown extension')
    INT = 'INT', _('Internal error')

    @classmethod
    def compare(cls, status1: Self, status2: Self):
        order = list(cls)
        return order.index(status1) - order.index(status2)


EMPTY_FINAL_STATUSES = [ResultStatus.EXT, ResultStatus.INT]


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


class SubmitType(models.TextChoices):
    STD = 'STD', _('Standard')
    HID = 'HID', _('Hidden')
    CTR = 'CTR', _('Control')
