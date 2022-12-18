from django.db import models
from django.db.models import Count

from BaCa2.choices import TaskJudgingMode, ResultStatus
from BaCa2.exceptions import ModelValidationError, DataError
from BaCa2.settings import BASE_DIR

SUBMITS_DIR = BASE_DIR / 'submits'


# "A round is a period of time in which a tasks can be submitted."
#
# The class has four fields:
#
# * start_date: The date and time when the round starts.
# * end_date: The date and time when ends possibility to gain max points.
# * deadline_date: The date and time when the round ends for submitting.
# * reveal_date: The date and time when the round results will be visible for everyone.
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
    package_instance = models.IntegerField()  # TODO: add foreign key
    task_name = models.CharField(max_length=1023)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    judging_mode = models.CharField(
        max_length=3,
        choices=TaskJudgingMode.choices,
        default=TaskJudgingMode.LIN
    )
    points = models.FloatField()

    def __str__(self):
        return f"Task {self.pk}: {self.task_name}; Judging mode: {TaskJudgingMode[self.judging_mode].label};" \
               f" Package: {self.package_instance}"


class TestSet(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    short_name = models.CharField(max_length=255)
    weight = models.FloatField()

    def __str__(self):
        return f"TestSet {self.pk}: Task/set: {self.task.task_name}/{self.short_name} (w: {self.weight})"


class Test(models.Model):
    short_name = models.CharField(max_length=255)
    test_set = models.ForeignKey(TestSet, on_delete=models.CASCADE)

    def __str__(self):
        return f"Test {self.pk}: Test/set/task: " \
               f"{self.short_name}/{self.test_set.short_name}/{self.test_set.task.task_name}"


# It's a model for a submit. It has a submit date, source code, task, user id, and final score
class Submit(models.Model):
    submit_date = models.DateTimeField(auto_now_add=True)
    source_code = models.FileField(upload_to=SUBMITS_DIR)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    usr = models.IntegerField()  # TODO: user id
    final_score = models.FloatField(default=-1)

    def __str__(self):
        return f"Submit {self.pk}: User: {self.usr}; Task: {self.task.task_name}; " \
               f"Score: {self.final_score if self.final_score > -1 else 'PENDING'}"

    def score(self, rejudge=False):
        """
        It calculates the score of a submit

        :param rejudge: If True, the score will be recalculated even if it was already calculated before,
        defaults to False (optional)
        :return: The score of the submit.
        """

        if rejudge:
            self.final_score = -1

        # It's a cache. If the score was already calculated, it will be returned without recalculating.
        if self.final_score != -1:
            return self.final_score

        # It counts amount of different statuses, grouped by test sets.
        results = (
            Result.objects
            .filter(submit=self)
            .values('test__test_set', 'status')
            .annotate(amount=Count('*'))
        )

        # It counts amount of tests in each test set.
        tests = (
            Test.objects
            .filter(test_set__task=self.task)
            .values('test_set')
            .annotate(amount=Count('*'))
        )

        # It's a dictionary, where keys are test sets, and values are dictionaries with keys:
        #         - MAX: amount of tests in test set
        #         - SUM: amount of results in test set
        #         - score: score of test set
        #         - [ResultStatus]: amount of statuses with that result.
        results_aggregated = {}
        for s in tests:
            results_aggregated[s['test_set']] = {'MAX': s['amount'], 'SUM': 0}

        for r in results:
            results_aggregated[r['test__test_set']][r['status']] = r['amount']
            results_aggregated[r['test__test_set']]['SUM'] += r['amount']

        judging_mode = self.task.judging_mode
        for test_set, s in results_aggregated.items():
            if s['SUM'] > s['MAX']:
                raise DataError(f"Submit ({self}): More test results, then test assigned to task")
            if s['SUM'] < s['MAX']:
                return -1

            # It's calculating the score of a submit, depending on judging mode.
            if judging_mode == TaskJudgingMode.LIN:
                results_aggregated[test_set]['score'] = s.get('OK', 0) / s['SUM']
            elif judging_mode == TaskJudgingMode.UNA:
                results_aggregated[test_set]['score'] = float(s.get('OK', 0) == s['SUM'])
            else:
                raise DataError(f"Submit ({self}): Task {self.task.pk} has invalid judging mode.")

        # It's calculating the score of a submit, as weighted average of sets scores.
        final_score = 0
        final_weight = 0
        for test_set, s in results_aggregated.items():
            final_weight += (weight := TestSet.objects.filter(pk=test_set).first().weight)
            final_score += s['score'] * weight

        self.final_score = round(final_score / final_weight, 6)
        return self.final_score


# `Result` is a class that represents a result of a test for a given submit and task (test set)
class Result(models.Model):  # TODO: +pola z kolejki
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=3,
        choices=ResultStatus.choices,
        default=ResultStatus.PND
    )

    def __str__(self):
        return f"Result {self.pk}: Set[{self.test.test_set.short_name}] Test[{self.test.short_name}]; " \
               f"Stat: {ResultStatus[self.status]}"
