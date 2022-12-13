from django.db import models
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from BaCa2.BaCa2.exceptions import ModelValidationError


class Round(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    deadline_date = models.DateTimeField()
    reveal_date = models.DateTimeField(null=True)

    @property
    def validate(self):
        if self.end_date is not None and (self.end_date <= self.start_date or self.deadline_date < self.end_date):
            raise ModelValidationError("Round: End date out of bounds of start date and deadline.")
        elif self.deadline_date <= self.start_date:
            raise ModelValidationError("Round: Start date can't be later then deadline.")

    def __str__(self):
        return f"Round {self.pk}"


class Task(models.Model):
    class TaskJudgingMode(models.TextChoices):
        LINEAR = 'L', _('Linear')
        UNANIMOUS = 'U', _('Unanimous')

    package_instance = models.IntegerField()  # TODO: add foreign key
    task_name = models.CharField(max_length=1023)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    judging_mode = models.CharField(
        max_length=1,
        choices=TaskJudgingMode.choices,
        default=TaskJudgingMode.LINEAR
    )

    def __str__(self):
        return f"Task {self.pk}: {self.task_name}. Judging mode: {self.TaskJudgingMode[self.judging_mode]}" \
               f" Package: {self.package_instance}"


class TestSet(models.Model):
    short_name = models.CharField(max_length=255)
    weight = models.FloatField()

    def __str__(self):
        return f"TestSet {self.pk}: {self.short_name} ({self.weight})"


class Test(models.Model):
    short_name = models.CharField(max_length=255)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    task_set = models.ForeignKey(TestSet, on_delete=models.CASCADE)

    def __str__(self):
        return f"Test {self.pk}/({self.task_set}): {self.short_name}"


class Submit(models.Model):
    submit_date = models.DateTimeField()
    source_code = models.FilePathField()
    task = models.ForeignKey(Test, on_delete=models.CASCADE)
    user = models.IntegerField()  # TODO: user id

    # TODO: scoring method
    # @property
    # def score(self):
    #     tests = (
    #         Result.objects
    #         .filter(user=self.user)
    #         .values(test__task_set__pk)
    #         .annotate(amount=Count('*'))
    #     )


class Result(models.Model):  # TODO: +pola z kolejki
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

    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=3,
        choices=ResultStatus.choices,
        default=ResultStatus.PND
    )

    def __str__(self):
        return f"Result {self.pk}: {self.test}, {self.submit}"
