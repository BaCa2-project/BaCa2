from typing import List, Self

from django.db import models, transaction
from django.db.models import Count, QuerySet
from django.core.exceptions import ValidationError

from BaCa2.choices import TaskJudgingMode, ResultStatus
from BaCa2.exceptions import DataError
from BaCa2.settings import SUBMITS_DIR

from main.models import User, Course

from package.models import PackageInstance
from baca2PackageManager import Package, TSet, TestF
from baca2PackageManager.broker_communication import BrokerToBaca

__all__ = ['Round', 'Task', 'TestSet', 'Test', 'Submit', 'Result']


class Round(models.Model):
    """
    A round is a period of time in which a tasks can be submitted.
    """

    #: The date and time when the round starts.
    start_date = models.DateTimeField()
    #: The date and time when ends possibility to gain max points.
    end_date = models.DateTimeField(null=True)
    #: The date and time when the round ends for submitting.
    deadline_date = models.DateTimeField()
    #: The date and time when the round results will be visible for everyone.
    reveal_date = models.DateTimeField(null=True)

    @property
    def validate(self):
        """
        If the end date is not None, then the end date must be greater than the start date and the deadline date must be
        greater than the end date. If the end date is None, then the deadline date must be greater than the start date.

        :raise ValidationError: If validation is not successful.
        """
        if self.end_date is not None and (self.end_date <= self.start_date or self.deadline_date < self.end_date):
            raise ValidationError("Round: End date out of bounds of start date and deadline.")
        elif self.deadline_date <= self.start_date:
            raise ValidationError("Round: Start date can't be later then deadline.")

    def __str__(self):
        return f"Round {self.pk}"


class Task(models.Model):
    """
    It represents a task that user can submit a solution to. The task is judged and scored automatically
    """

    #: Pseudo-foreign key to package instance.
    package_instance_id = models.BigIntegerField(validators=[PackageInstance.exists])
    #: Represents displayed task name
    task_name = models.CharField(max_length=1023)
    #: Foreign key to round, which task is assigned to.
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    #: Judging mode as choice from BaCa2.choices.TaskJudgingMode (enum-type choice)
    judging_mode = models.CharField(
        max_length=3,
        choices=TaskJudgingMode.choices,
        default=TaskJudgingMode.LIN
    )
    #: Maximum amount of points to be earned by completing this task.
    points = models.FloatField()

    def __str__(self):
        return f"Task {self.pk}: {self.task_name}; Judging mode: {TaskJudgingMode[self.judging_mode].label};" \
               f"Package: {self.package_instance}"

    def initialise_task(self) -> None:
        """
        It initialises the task by creating a new instance of the Task class, and adding all task sets and tests to db.

        :return: None
        """
        pkg = self.package_instance.package
        for t_set in pkg.sets():
            TestSet.create_from_package(t_set, self)

    @classmethod
    def create_new(cls, initialise=True, **kwargs) -> 'Task':
        """
        If the user passes in a PackageInstance object, we'll use the object's primary key as the value for the
        package_instance_id field.

        :return: A new instance of the class.
        """
        pkg_instance = kwargs.get('package_instance')
        if isinstance(pkg_instance, PackageInstance):
            kwargs['package_instance_id'] = pkg_instance.pk
            del kwargs['package_instance']
        pkg_instance = kwargs.get('package_instance_id')
        if isinstance(pkg_instance, PackageInstance):
            kwargs['package_instance_id'] = pkg_instance.pk

        task_obj = cls.objects.create(**kwargs)
        task_obj.save()
        if initialise:
            task_obj.initialise_task()
        return task_obj

    @property
    def sets(self) -> QuerySet:
        """
        It returns all the test sets that are associated with the task

        :return: A list of all the TestSet objects that are associated with the Task object.
        """
        return TestSet.objects.filter(task=self).all()

    @property
    def package_instance(self) -> PackageInstance:
        """
        It returns the package instance associated with the current package instance

        :return: A PackageInstance object.
        """
        return PackageInstance.objects.get(pk=self.package_instance_id)

    def last_submit(self, usr, amount=1) -> 'Submit' | List['Submit']:
        """
        It returns the last submit of a user for a task or a list of 'amount' last submits to that task.

        :param usr: The user who submitted the task
        :param amount: The amount of submits to return, defaults to 1 (optional)
        :return: The last submit of a user for a task.
        """
        if amount == 1:
            return Submit.objects.filter(task=self, usr=usr.pk).order_by('-submit_date').first()
        return Submit.objects.filter(task=self, usr=usr.pk).order_by('-submit_date').all()[:amount]

    def best_submit(self, usr, amount=1) -> 'Submit' | List['Submit']:
        """
        It returns the best submit of a user for a task or list of 'amount' best submits to that task.

        :param usr: The user who submitted the solution
        :param amount: The amount of submits you want to get, defaults to 1 (optional)
        :return: The best submit of a user for a task.
        """
        if amount == 1:
            return Submit.objects.filter(task=self, usr=usr.pk).order_by('-final_score').first()
        return Submit.objects.filter(task=self, usr=usr.pk).order_by('-final_score').all()[:amount]

    @classmethod
    def check_instance(cls, pkg_instance: PackageInstance, in_every_course: bool = True) -> bool:
        """
        Check if a package instance exists in every course, optionally checking in context given course

        :param cls: the class of the model you're checking for
        :param pkg_instance: The PackageInstance object that you want to check for
        :type pkg_instance: PackageInstance
        :param in_every_course: If True, the package instance must be in every course.
        If False, it must be in at least one course, defaults to True
        :type in_every_course: bool (optional)
        :return: A boolean value.
        """
        if not in_every_course:
            return cls.objects.filter(package_instance_id=pkg_instance.pk).exists()

        # check in every course
        from .routing import InCourse
        courses = Course.objects.all()
        for course in courses:
            with InCourse(course):
                if cls.objects.filter(package_instance_id=pkg_instance.pk).exists():
                    return True
        return False


class TestSet(models.Model):
    """
    Model groups single tests into a set of tests. Gives them a set name, and weight, used while calculating results for
    whole task.
    """

    #: Foreign key to task, with which tests set is associated.
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    #: Name of set - short description of test set (f.e. "n<=40", where n stands for task parameter)
    short_name = models.CharField(max_length=255)
    #: Weight of test set in final task result.
    weight = models.FloatField()

    def __str__(self):
        return f"TestSet {self.pk}: Task/set: {self.task.task_name}/{self.short_name} (w: {self.weight})"

    @classmethod
    def create_from_package(cls, t_set: TSet, task: Task) -> Self:
        """
        It creates a new TestSet object from a TSet object.

        :param t_set: The TSet object that you want to create a TestSet object from.
        :type t_set: TSet
        :param task: The task that you want to associate the TestSet object with.
        :type task: Task

        :return: A new TestSet object.
        :rtype: TestSet
        """
        test_set = cls.objects.create(short_name=t_set['name'], weight=t_set['weight'], task=task)
        test_set.save()
        for test in t_set.tests():
            Test.create_from_package(test, test_set)
        return test_set

    @property
    def tests(self) -> QuerySet:
        """
        It returns all the tests that are associated with the test set

        :return: A list of all the tests in the test set.
        """
        return Test.objects.filter(test_set=self).all()


class Test(models.Model):
    """
    Single test. Primary object to be connected with students' results.
    """

    #: Simple description what exactly is tested. Corresponds to :py:class:`package.package_manage.TestF`.
    short_name = models.CharField(max_length=255)
    #: Foreign key to :py:class:`TestSet`.
    test_set = models.ForeignKey(TestSet, on_delete=models.CASCADE)

    @classmethod
    def create_from_package(cls, test: TestF, test_set: TestSet) -> Self:
        """
        It creates a new Test object from a TestF object.

        :param test: The TestF object that you want to create a Test object from.
        :type test: TestF
        :param test_set: The test set that you want to associate the Test object with.
        :type test_set: TestSet

        :return: A new Test object.
        :rtype: Test
        """
        return cls.objects.create(short_name=test['name'], test_set=test_set)

    def __str__(self):
        return f"Test {self.pk}: Test/set/task: " \
               f"{self.short_name}/{self.test_set.short_name}/{self.test_set.task.task_name}"


class Submit(models.Model):
    """
    Model containing single submit information. It is assigned to task and user.
    """

    #: Datetime when submit took place.
    submit_date = models.DateTimeField(auto_now_add=True)
    #: Field submitted to the task
    source_code = models.FilePathField(path=SUBMITS_DIR, allow_files=True)
    #: :py:class:`Task` model, to which submit is assigned.
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    #: Pseudo-foreign key to :py:class:`main.models.User` model (user), who submitted to the task.
    usr = models.BigIntegerField(validators=[User.exists])
    #: Final score (as percent), gained by user's submission. Before solution check score is set to ``-1``.
    final_score = models.FloatField(default=-1)

    @classmethod
    def create_new(cls, **kwargs) -> Self:
        """
        Creates new Submit, but changes ``usr`` attribute to its primary key, when passed as model. This is because of
        simulating Primary Key for user.

        :return: New created submit.
        """
        user = kwargs.get('usr')
        if isinstance(user, User):
            kwargs['usr'] = user.pk
        return cls.objects.create(**kwargs)

    @property
    def user(self) -> User:
        """
        Simulates user model for Submit.

        :return: Returns user model
        """
        return User.objects.get(pk=self.usr)

    def __str__(self):
        return f"Submit {self.pk}: User: {self.user}; Task: {self.task.task_name}; " \
               f"Score: {self.final_score if self.final_score > -1 else 'PENDING'}"

    def score(self, rejudge: bool = False) -> float:
        """
        It calculates the score of *self* submit.

        :param rejudge: If True, the score will be recalculated even if it was already calculated before,
            defaults to False (optional)
        :type rejudge: bool
        :return: The score of the submit.
        :raise DataError: if there is more results than tests
        :raise NotImplementedError: if selected judging mode is not implemented
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
                raise NotImplementedError(f"Submit ({self}): Task {self.task.pk} has judging mode " +
                                          f"which is not implemented.")

        # It's calculating the score of a submit, as weighted average of sets scores.
        final_score = 0
        final_weight = 0
        for test_set, s in results_aggregated.items():
            final_weight += (weight := TestSet.objects.filter(pk=test_set).first().weight)
            final_score += s['score'] * weight

        self.final_score = round(final_score / final_weight, 6)
        return self.final_score


class Result(models.Model):  # TODO: +pola z kolejki
    """
    Result of single :py:class:`Test` testing.
    """

    #: :py:class:`Test` which is scored.
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    #: :py:class:`Submit` model this test is connected to.
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)
    #: Status result. Described as one of choices from :py:class:`BaCa2.choices.ResultStatus`
    status = models.CharField(
        max_length=3,
        choices=ResultStatus.choices,
        default=ResultStatus.PND
    )
    #: Time of test execution in seconds.
    time_real = models.FloatField(null=True, default=None)
    #: Time of test execution in seconds, measured by CPU.
    time_cpu = models.FloatField(null=True, default=None)
    #: Memory used by test in bytes.
    runtime_memory = models.IntegerField(null=True, default=None)

    @classmethod
    @transaction.atomic
    def unpack_results(cls, submit_id, results: BrokerToBaca) -> None:
        """
        It unpacks the results from the BrokerToBaca object and saves them to the database.

        :param submit_id: The submit id that you want to unpack the results for.
        :type submit_id: str
        :param results: The BrokerToBaca object that you want to unpack the results from.
        :type results: BrokerToBaca

        :return: None
        """
        submit = Submit.objects.get(pk=submit_id)
        for set_name, set_result in results.results.items():
            test_set = TestSet.objects.get(task=submit.task, short_name=set_name)
            for test_name, test_result in set_result.tests.items():
                test = Test.objects.get(test_set=test_set, short_name=test_name)
                cls.objects.create(
                    test=test,
                    submit=submit,
                    status=test_result.status,
                    time_real=test_result.time_real,
                    time_cpu=test_result.time_cpu,
                    runtime_memory=test_result.runtime_memory,
                )

    def __str__(self):
        return f"Result {self.pk}: Set[{self.test.test_set.short_name}] Test[{self.test.short_name}]; " \
               f"Stat: {ResultStatus[self.status]}"
