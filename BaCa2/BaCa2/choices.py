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
