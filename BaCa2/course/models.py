from django.db import models
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
    package_instance = models.IntegerField()  # TODO: add foreign key
    task_name = models.CharField(max_length=1023)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)

    def __str__(self):
        return f"Task {self.pk}: {self.task_name}. Package: {self.package_instance}"


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


class Result(models.Model):  # TODO: +pola z kolejki
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)

    def __str__(self):
        return f"Result {self.pk}: {self.test}, {self.submit}"

