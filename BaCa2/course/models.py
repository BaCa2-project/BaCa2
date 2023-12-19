from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Self, Any, TYPE_CHECKING

from django.db import models, transaction
from django.db.models import Count, QuerySet
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from BaCa2.choices import TaskJudgingMode, ResultStatus
from BaCa2.exceptions import DataError
from BaCa2.settings import SUBMITS_DIR
from course.routing import OptionalInCourse
from baca2PackageManager import Package, TSet, TestF
from baca2PackageManager.broker_communication import BrokerToBaca

from util.models_registry import ModelsRegistry

if TYPE_CHECKING:
    from main.models import User, Course
    from package.models import PackageInstance

__all__ = ['Round', 'Task', 'TestSet', 'Test', 'Submit', 'Result']


class RoundManager(models.Manager):

    @transaction.atomic
    def create_round(self,
                     start_date: datetime,
                     deadline_date: datetime,
                     end_date: datetime = None,
                     reveal_date: datetime = None,
                     course: str | int | Course = None) -> Round:
        """
        It creates a new round object, but validates it first.

        :param start_date: The start date of the round.
        :type start_date: datetime
        :param deadline_date: The deadline date of the round.
        :type deadline_date: datetime
        :param end_date: The end date of the round, defaults to None (optional)
        :type end_date: datetime
        :param reveal_date: The results reveal date for the round, defaults to None (optional)
        :type reveal_date: datetime
        :param course: The course that the round is in, if None - acquired from external definition
            (optional)
        :type course: str | int | Course

        :return: A new round object.
        :rtype: Round
        """
        Round.validate_dates(start_date, deadline_date, end_date)
        with OptionalInCourse(course):
            new_round = self.model(start_date=start_date,
                                   deadline_date=deadline_date,
                                   end_date=end_date,
                                   reveal_date=reveal_date)
            new_round.save()
            return new_round

    @transaction.atomic
    def delete_round(self, round_: int | Round, course: str | int | Course = None) -> None:
        """
        It deletes a round object.

        :param round_: The round id that you want to delete.
        :type round_: int
        :param course: The course that the round is in, defaults to None (optional)
        :type course: str | int | Course
        """
        with OptionalInCourse(course):
            ModelsRegistry.get_round(round_).delete()

    def all_rounds(self) -> List[Round]:
        """
        It returns all the rounds.

        :return: A list of all the Round objects.
        :rtype: List[Round]
        """
        return list(self.all())


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

    #: The manager for the Round model.
    objects = RoundManager()

    @staticmethod
    def validate_dates(start_date: datetime,
                       deadline_date: datetime,
                       end_date: datetime = None) -> None:
        """
        If the end date is not None, then the end date must be greater than the start date and the deadline date must be
        greater than the end date. If the end date is None, then the deadline date must be greater than the start date.

        :param start_date: The start date of the round.
        :type start_date: datetime
        :param deadline_date: The deadline date of the round.
        :type deadline_date: datetime
        :param end_date: The end date of the round, defaults to None (optional)
        :type end_date: datetime

        :raise ValidationError: If validation is not successful.
        """
        if end_date is not None and (end_date <= start_date or deadline_date < end_date):
            raise ValidationError("Round: End date out of bounds of start date and deadline.")
        elif deadline_date <= start_date:
            raise ValidationError("Round: Start date can't be later then deadline.")

    @transaction.atomic
    def delete(self, using: Any = None, keep_parents: bool = False):
        """
        It deletes the round object.
        """
        tasks = Task.objects.filter(round=self).all()
        for task in tasks:
            task.delete()
        super().delete(using, keep_parents)

    @property
    def is_open(self) -> bool:
        """
        It checks if the round is open.

        :return: A boolean value.
        :rtype: bool
        """
        return self.start_date <= now() <= self.deadline_date

    @property
    def tasks(self) -> QuerySet:
        """
        It returns all the tasks that are associated with the round

        :return: A list of all the Task objects that are associated with the Round object.
        :rtype: QuerySet
        """
        return Task.objects.filter(round=self).all()

    @property
    def round_points(self) -> float:
        """
        It returns the amount of points that can be gained for completing all the tasks in the round.

        :return: The amount of points that can be gained for completing all the tasks in the round.
        """
        return sum(task.points for task in self.tasks)

    def __str__(self):
        return f"Round {self.pk}"


class TaskManager(models.Manager):

    @transaction.atomic
    def create_task(self,
                    package_instance: int | PackageInstance,
                    round_: int | Round,
                    task_name: str,
                    points: float,
                    judging_mode: str | TaskJudgingMode = TaskJudgingMode.LIN,
                    initialise_task: bool = True,
                    course: str | int | Course = None) -> Task:
        """
        It creates a new task object, and (if `initialise_task` is True) initialises it using
        data from `PackageManager`.

        :param package_instance: The package instance that you want to associate the task with.
        :type package_instance: int | PackageInstance
        :param round_: The round that you want to associate the task with.
        :type round_: int | Round
        :param task_name: The name of the task.
        :type task_name: str
        :param points: The amount of points that you can get for completing the task.
        :type points: float
        :param judging_mode: The judging mode of the task, defaults to
            TaskJudgingMode.LIN (optional)
        :type judging_mode: TaskJudgingMode
        :param initialise_task: If True, the task will be initialised using data from
            PackageManager, otherwise sub-objects (tasks, sets & tests) won't be created
        defaults to True (optional)
        :type initialise_task: bool
        :param course: The course that the task is in, if None - acquired from external definition
            (optional)
        :type course: str | int | Course

        :return: A new task object.
        :rtype: Task
        """
        package_instance = ModelsRegistry.get_package_instance(package_instance)
        round_ = ModelsRegistry.get_round(round_)
        judging_mode = ModelsRegistry.get_task_judging_mode(judging_mode)
        with OptionalInCourse(course):
            new_task = self.model(package_instance_id=package_instance.pk,
                                  task_name=task_name,
                                  round=round_,
                                  judging_mode=judging_mode,
                                  points=points)
            new_task.save()
            if initialise_task:
                new_task.initialise_task()
            return new_task

    @transaction.atomic
    def delete_task(self, task: int | Task, course: str | int | Course = None) -> None:
        """
        It deletes a task object (with all the test sets and tests that are associated with it).

        :param task: The task id that you want to delete.
        :type task: int
        :param course: The course that the task is in, if None - acquired from external definition
            (optional)
        :type course: str | int | Course
        """
        task = ModelsRegistry.get_task(task, course)
        with OptionalInCourse(course):
            task.delete()

    @staticmethod
    def package_instance_exists_validator(package_instance: int) -> bool:
        """
        It checks if a package instance exists.

        :param package_instance: The package instance id that you want to check.
        :type package_instance: int | PackageInstance

        :return: A boolean value.
        :rtype: bool
        """
        from package.models import PackageInstance
        return PackageInstance.objects.exists_validator(package_instance)


class Task(models.Model):
    """
    It represents a task that user can submit a solution to. The task is judged and scored automatically
    """

    #: Pseudo-foreign key to package instance.
    package_instance_id = models.BigIntegerField(
        validators=[TaskManager.package_instance_exists_validator])
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

    #: The manager for the Task model.
    objects = TaskManager()

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
            TestSet.objects.create_from_package(t_set, self)

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        It deletes the task object, and all the test sets and tests that are associated with it.
        """
        for t_set in self.sets:
            t_set.delete()
        super().delete(using, keep_parents)

    @property
    def sets(self) -> QuerySet:
        """
        It returns all the test sets that are associated with the task

        :return: A list of all the TestSet objects that are associated with the Task object.
        """
        return TestSet.objects.filter(task=self).all()

    @property
    def sets_amount(self) -> int:
        """
        It returns the amount of test sets that are associated with the task

        :return: The amount of TestSet objects that are associated with the Task object.
        """
        return TestSet.objects.filter(task=self).count()

    @property
    def tests_amount(self) -> int:
        """
        It returns the amount of tests that are associated with the task

        :return: The amount of Test objects that are associated with the Task object.
        """
        return Test.objects.filter(test_set__task=self).count()

    @property
    def package_instance(self) -> PackageInstance:
        """
        It returns the package instance associated with the current package instance

        :return: A PackageInstance object.
        """
        from package.models import PackageInstance
        return PackageInstance.objects.get(pk=self.package_instance_id)

    @transaction.atomic
    def refresh_user_submits(self, user: str | int | User, rejudge: bool = False) -> None:
        """
        It refreshes the submits' scores for a user for a task. If rejudge is True, the score will
        be recalculated even if it was already calculated before.

        :param user: The user who submitted the task
        :type user: str | int | User
        :param rejudge: If True, the score will be recalculated even if it was already calculated
            before, defaults to False (optional)
        :type rejudge: bool
        """
        user = ModelsRegistry.get_user(user)
        for submit in Submit.objects.filter(task=self, usr=user.pk).all():
            submit.score(rejudge=rejudge)

    def last_submit(self, user: str | int | User, amount=1) -> Submit | List[Submit]:
        """
        It returns the last submit of a user for a task or a list of 'amount' last submits to that task.

        :param user: The user who submitted the task
        :type user: str | int | User
        :param amount: The amount of submits to return, defaults to 1 (optional)
        :type amount: int

        :return: The last submit of a user for a task.
        """
        user = ModelsRegistry.get_user(user)
        self.refresh_user_submits(user)
        if amount == 1:
            return Submit.objects.filter(task=self, usr=user.pk).order_by('-submit_date').first()
        return Submit.objects.filter(task=self, usr=user.pk).order_by('-submit_date').all()[:amount]

    def best_submit(self, user: str | int | User, amount=1) -> Submit | List[Submit]:
        """
        It returns the best submit of a user for a task or list of 'amount' best submits to that
        task.

        :param user: The user who submitted the solution
        :type user: str | int | User
        :param amount: The amount of submits you want to get, defaults to 1 (optional)
        :type amount: int

        :return: The best submit of a user for a task.
        """
        user = ModelsRegistry.get_user(user)
        self.refresh_user_submits(user)
        if amount == 1:
            return Submit.objects.filter(task=self, usr=user.pk).order_by('-final_score').first()
        return Submit.objects.filter(task=self, usr=user.pk).order_by('-final_score').all()[:amount]

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
        from main.models import Course
        courses = Course.objects.all()
        for course in courses:
            with InCourse(course):
                if cls.objects.filter(package_instance_id=pkg_instance.pk).exists():
                    return True
        return False


class TestSetManager(models.Manager):

    @transaction.atomic
    def create_test_set(self, task: int | Task, short_name: str, weight: float) -> TestSet:
        """
        It creates a new test set object.

        :param task: The task that you want to associate the test set with.
        :type task: int | Task
        :param short_name: The short name of the test set.
        :type short_name: str
        :param weight: The weight of the test set.
        :type weight: float

        :return: A new test set object.
        :rtype: TestSet

        :raise ValidationError: If test set with given short name already exists under chosen task.
        """
        task = ModelsRegistry.get_task(task)
        sets = task.sets
        if sets.filter(short_name=short_name).exists():
            raise ValidationError(f"TestSet: Test set with short name {short_name} already exists.")

        new_test_set = self.model(short_name=short_name,
                                  weight=weight,
                                  task=task)
        new_test_set.save()
        return new_test_set

    @transaction.atomic
    def delete_test_set(self, test_set: int | TestSet, course: str | int | Course = None) -> None:
        """
        It deletes a test set object.

        :param test_set: The test set id that you want to delete.
        :type test_set: int
        :param course: The course that the test set is in, defaults to None (optional)
        :type course: str | int | Course
        """
        test_set = ModelsRegistry.get_test_set(test_set, course)
        test_set.delete()

    @transaction.atomic
    def create_from_package(self, t_set: TSet, task: Task) -> TestSet:
        """
        It creates a new TestSet object from a TSet object.

        :param t_set: The TSet object that you want to create a TestSet object from.
        :type t_set: TSet
        :param task: The task that you want to associate the TestSet object with.
        :type task: Task

        :return: A new TestSet object.
        :rtype: TestSet
        """
        test_set = self.model(short_name=t_set['name'],
                              weight=t_set['weight'],
                              task=task)
        test_set.save()
        for test in t_set.tests():
            Test.objects.create_from_package(test, test_set)
        return test_set


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

    #: The manager for the TestSet model.
    objects = TestSetManager()

    def __str__(self):
        return f"TestSet {self.pk}: Task/set: {self.task.task_name}/{self.short_name} (w: {self.weight})"

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        It deletes the TestSet object, and all the tests that are associated with it.
        """
        for test in self.tests:
            test.delete()
        super().delete(using, keep_parents)

    @property
    def tests(self) -> QuerySet:
        """
        It returns all the tests that are associated with the test set

        :return: A list of all the tests in the test set.
        """
        return Test.objects.filter(test_set=self).all()


class TestManager(models.Manager):

    @transaction.atomic
    def create_test(self, short_name: str, test_set: TestSet) -> Test:
        """
        It creates a new test object.

        :param short_name: The short name of the test.
        :type short_name: str
        :param test_set: The test set that you want to associate the test with.
        :type test_set: TestSet

        :return: A new test object.
        :rtype: Test
        """
        new_test = self.model(short_name=short_name,
                              test_set=test_set)
        new_test.save()
        return new_test

    @transaction.atomic
    def delete_test(self, test: int | Test, course: str | int | Course = None) -> None:
        """
        It deletes a test object.

        :param test: The test id that you want to delete.
        :type test: int
        :param course: The course that the test is in, defaults to None (optional)
        :type course: str | int | Course
        """
        test_to_delete = ModelsRegistry.get_test(test, course)
        test_to_delete.delete()

    @transaction.atomic
    def create_from_package(self, test: TestF, test_set: TestSet) -> Test:
        """
        It creates a new Test object from a TestF object.

        :param test: The TestF object that you want to create a Test object from.
        :type test: TestF
        :param test_set: The test set that you want to associate the Test object with.
        :type test_set: TestSet

        :return: A new Test object.
        :rtype: Test
        """
        return self.create_test(short_name=test['name'], test_set=test_set)


class Test(models.Model):
    """
    Single test. Primary object to be connected with students' results.
    """

    #: Simple description what exactly is tested. Corresponds to py:class:`package.package_manage.TestF`.
    short_name = models.CharField(max_length=255)
    #: Foreign key to :py:class:`TestSet`.
    test_set = models.ForeignKey(TestSet, on_delete=models.CASCADE)

    #: The manager for the Test model.
    objects = TestManager()

    def __str__(self):
        return f"Test {self.pk}: Test/set/task: " \
               f"{self.short_name}/{self.test_set.short_name}/{self.test_set.task.task_name}"

    @property
    def associated_results(self) -> QuerySet:
        """
        Returns all results associated with this test.

        :return: QuerySet of results
        :rtype: QuerySet
        """
        return Result.objects.filter(test=self).all()

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        It deletes the Test object, and all the results that are associated with it.
        """
        for result in self.associated_results:
            result.delete()
        super().delete(using, keep_parents)


class SubmitManager(models.Manager):
    @transaction.atomic
    def create_submit(self,
                      source_code: str | Path,
                      task: int | Task,
                      user: str | int | User,
                      submit_date: datetime = now(),
                      final_score: float = -1) -> Submit:
        """
        It creates a new submit object.

        :param source_code: The path to the source code file.
        :type source_code: str | Path
        :param task: The task that you want to associate the submit with.
        :type task: int | Task
        :param user: The user that you want to associate the submit with.
        :type user: str | int | User
        :param submit_date: The date and time when the submit was created, defaults to now() (optional)
        :type submit_date: datetime
        :param final_score: The final score of the submit, defaults to -1 (optional)
        :type final_score: float

        :return: A new submit object.
        :rtype: Submit
        """
        task = ModelsRegistry.get_task(task)
        user = ModelsRegistry.get_user(user)
        source_code = ModelsRegistry.get_source_code(source_code)
        new_submit = self.model(submit_date=submit_date,
                                source_code=source_code,
                                task=task,
                                usr=user.pk,
                                final_score=final_score)
        new_submit.save()
        return new_submit

    @transaction.atomic
    def delete_submit(self, submit: int | Submit, course: str | int | Course = None) -> None:
        """
        It deletes a submit object.

        :param submit: The submit id that you want to delete.
        :type submit: int
        :param course: The course that the submit is in, defaults to None (optional)
        :type course: str | int | Course
        """
        submit = ModelsRegistry.get_submit(submit, course)
        submit.delete()

    @staticmethod
    def user_exists_validator(user: int) -> bool:
        """
        It checks if a user exists.

        :param user: The user id that you want to check.
        :type user: int

        :return: A boolean value.
        :rtype: bool
        """
        from main.models import User
        return User.exists(user)


class Submit(models.Model):
    """
    Model containing single submit information. It is assigned to task and user.
    """

    #: Datetime when submit took place.
    submit_date = models.DateTimeField(auto_now_add=True)
    #: Field submitted to the task
    source_code = models.FilePathField(path=SUBMITS_DIR, allow_files=True, null=True)
    #: :py:class:`Task` model, to which submit is assigned.
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    #: Pseudo-foreign key to :py:class:`main.models.User` model (user), who submitted to the task.
    usr = models.BigIntegerField(validators=[SubmitManager.user_exists_validator])
    #: Final score (as percent), gained by user's submission. Before solution check score is set to ``-1``.
    final_score = models.FloatField(default=-1)

    #: The manager for the Submit model.
    objects = SubmitManager()

    def send(self):
        """
        It sends the submit to the broker.

        :return: None
        """
        raise NotImplementedError("This method is not implemented yet.")
        # TODO: Submit sending to broker

    def delete(self, using=None, keep_parents=False):
        """
        It deletes the submit object, and all the results that are associated with it.
        """
        for result in self.results:
            result.delete()
        super().delete(using, keep_parents)

    @property
    def user(self) -> User:
        """
        Simulates user model for Submit.

        :return: Returns user model
        """
        from main.models import User
        return User.objects.get(pk=self.usr)

    def __str__(self):
        return f"Submit {self.pk}: User: {self.user}; Task: {self.task.task_name}; " \
               f"Score: {self.final_score if self.final_score > -1 else 'PENDING'}"

    @property
    def results(self) -> QuerySet:
        """
        Returns all results associated with this submit.

        :return: QuerySet of results
        :rtype: QuerySet
        """
        return Result.objects.filter(submit=self).all()

    @transaction.atomic()
    def score(self, rejudge: bool = False) -> float:
        """
        It calculates the score of *self* submit.

        :param rejudge: If True, the score will be recalculated even if it was already calculated
        before, defaults to False (optional)
        :type rejudge: bool

        :return: The score of the submit.

        :raise DataError: if there is more results than tests
        :raise NotImplementedError: if selected judging mode is not implemented
        """

        if rejudge:
            self.final_score = -1

        # It's a cache. If the score was already calculated, it will be returned without recalculating.
        if self.final_score >= 0:
            return self.final_score

        if self.results.count() < self.task.tests_amount:
            self.final_score = -1
            self.save()
            return -1

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
                raise NotImplementedError(
                    f"Submit ({self}): Task {self.task.pk} has judging mode " +
                    f"which is not implemented.")

        # It's calculating the score of a submit, as weighted average of sets scores.
        final_score = 0
        final_weight = 0
        for test_set, s in results_aggregated.items():
            final_weight += (weight := TestSet.objects.filter(pk=test_set).first().weight)
            final_score += s['score'] * weight

        self.final_score = round(final_score / final_weight, 6)
        self.save()
        return self.final_score


class ResultManager(models.Manager):
    @transaction.atomic
    def unpack_results(self,
                       submit: int | Submit,
                       results: BrokerToBaca,
                       auto_score: bool = True) -> List[Result]:
        """
        It unpacks the results from the BrokerToBaca object and saves them to the database.

        :param submit: The submit id that you want to unpack the results for.
        :type submit: int | Submit
        :param results: The BrokerToBaca object that you want to unpack the results from.
        :type results: BrokerToBaca
        :param auto_score: If True, the score of the submit will be calculated automatically,
            defaults to True (optional)
        :type auto_score: bool

        :return: None
        """
        submit = ModelsRegistry.get_submit(submit)
        results_list = []

        for set_name, set_result in results.results.items():
            test_set = TestSet.objects.get(task=submit.task, short_name=set_name)
            for test_name, test_result in set_result.tests.items():
                test = Test.objects.get(test_set=test_set, short_name=test_name)
                result = self.model(
                    test=test,
                    submit=submit,
                    status=test_result.status,
                    time_real=test_result.time_real,
                    time_cpu=test_result.time_cpu,
                    runtime_memory=test_result.runtime_memory,
                )
                result.save()
                results_list.append(result)
        if auto_score:
            submit.score(rejudge=True)
        return results_list

    @transaction.atomic
    def create_result(self,
                      test: int | Test,
                      submit: int | Submit,
                      status: str | ResultStatus = ResultStatus.PND,
                      time_real: float = None,
                      time_cpu: float = None,
                      runtime_memory: int = None) -> Result:
        """
        It creates a new result object.

        :param test: The test that you want to associate the result with.
        :type test: int | Test
        :param submit: The submit that you want to associate the result with.
        :type submit: int | Submit
        :param status: The status of the result, defaults to ResultStatus.PND (optional)
        :type status: str | ResultStatus
        :param time_real: The real time of the result, defaults to None (optional)
        :type time_real: float
        :param time_cpu: The cpu time of the result, defaults to None (optional)
        :type time_cpu: float
        :param runtime_memory: The runtime memory of the result, defaults to None (optional)
        :type runtime_memory: int

        :return: A new result object.
        :rtype: Result
        """
        test = ModelsRegistry.get_test(test)
        submit = ModelsRegistry.get_submit(submit)
        status = ModelsRegistry.get_result_status(status)
        new_result = self.model(test=test,
                                submit=submit,
                                status=status,
                                time_real=time_real,
                                time_cpu=time_cpu,
                                runtime_memory=runtime_memory)
        new_result.save()
        return new_result

    @transaction.atomic
    def delete_result(self, result: int | Result, course: str | int | Course = None) -> None:
        """
        It deletes a result object.

        :param result: The result id that you want to delete.
        :type result: int
        :param course: The course that the result is in, defaults to None (optional)
        :type course: str | int | Course
        """
        result = ModelsRegistry.get_result(result, course)
        result.delete()


class Result(models.Model):
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

    #: The manager for the Result model.
    objects = ResultManager()

    def __str__(self):
        return f"Result {self.pk}: Set[{self.test.test_set.short_name}] Test[{self.test.short_name}]; " \
               f"Stat: {ResultStatus[self.status]}"

    def delete(self, using=None, keep_parents=False, rejudge: bool = False):
        """
        It deletes the result object.
        """
        super().delete(using, keep_parents)
        if rejudge:
            self.submit.score(rejudge=True)
