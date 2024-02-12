from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count
from django.db.models.base import ModelBase
from django.utils.timezone import now

from baca2PackageManager import TestF, TSet
from baca2PackageManager.broker_communication import BrokerToBaca
from core.choices import ModelAction, ResultStatus, TaskJudgingMode
from core.exceptions import DataError
from course.routing import InCourse, OptionalInCourse
from util.models_registry import ModelsRegistry

if TYPE_CHECKING:
    from broker_api.models import BrokerSubmit
    from main.models import Course, User
    from package.models import PackageInstance

__all__ = ['Round', 'Task', 'TestSet', 'Test', 'Submit', 'Result']


class ReadCourseMeta(ModelBase):
    """
    Metaclass providing automated database routing for all course objects.
    If object was acquired from specific database, all operations are performed inside
    of this database.
    """
    DECORATOR_OFF = []

    def __new__(cls, name, bases, dct):
        """
        Creates new class with the same name, base and dictionary, but wraps all non-static,
        non-class methods and properties with :py:meth`read_course_decorator`

        *Special method signature from* ``django.db.models.base.ModelBase``
        """
        result_class = super().__new__(cls, name, bases, dct)

        # Decorate all non-static, non-class methods with the hook method
        for attr_name, attr_value in dct.items():
            if all(((callable(attr_value) or isinstance(attr_value, property)),
                    not attr_name.startswith('_'),
                    not isinstance(attr_value, classmethod),
                    not isinstance(attr_value, staticmethod),
                    not inspect.isclass(attr_value),
                    attr_name not in cls.DECORATOR_OFF)):
                decorated_meth = cls.read_course_decorator(attr_value,
                                                           isinstance(attr_value, property))
                decorated_meth.__doc__ = attr_value.__doc__
                setattr(result_class,
                        attr_name,
                        decorated_meth)
        return result_class

    @staticmethod
    def read_course_decorator(original_method, prop: bool = False):
        """
        Decorator used to decode origin database from object. It wraps every operation inside
        the object to be performed on meta-read database.

        :param original_method: Original method to be wrapped
        :param prop: Indicates if original method is a property.
        :type prop: bool

        :returns: Wrapped method

        """

        def wrapper_method(self, *args, **kwargs):
            if InCourse.is_defined():
                result = original_method(self, *args, **kwargs)
            else:
                with InCourse(self._state.db):
                    result = original_method(self, *args, **kwargs)
            return result

        def wrapper_property(self):
            if InCourse.is_defined():
                result = original_method.fget(self)
            else:
                with InCourse(self._state.db):
                    result = original_method.fget(self)
            return result

        if prop:
            return property(wrapper_property)
        return wrapper_method


class RoundManager(models.Manager):

    @transaction.atomic
    def create_round(self,
                     start_date: datetime,
                     deadline_date: datetime,
                     name: str = None,
                     end_date: datetime = None,
                     reveal_date: datetime = None,
                     course: str | int | Course = None) -> Round:
        """
        It creates a new round object, but validates it first.

        :param start_date: The start date of the round.
        :type start_date: datetime
        :param deadline_date: The deadline date of the round.
        :type deadline_date: datetime
        :param name: The name of the round, defaults to ``Round <nb>`` (optional)
        :type name: str
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
        if name is None:
            name = self.default_round_name
        with OptionalInCourse(course):
            new_round = self.model(start_date=start_date,
                                   deadline_date=deadline_date,
                                   name=name,
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

    @property
    def default_round_name(self) -> str:
        """
        It returns the default round name.

        :return: The default round name.
        :rtype: str
        """
        return f'Round {self.count() + 1}'


class Round(models.Model, metaclass=ReadCourseMeta):
    """
    A round is a period of time in which a tasks can be submitted.
    """

    #: Name of round
    name = models.CharField(max_length=2047, default='<no-name>')
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

    class BasicAction(ModelAction):
        """
        Basic actions for Round model.
        """
        ADD = 'add', 'add_round'
        DEL = 'delete', 'delete_round'
        EDIT = 'edit', 'change_round'
        VIEW = 'view', 'view_round'

    @staticmethod
    def validate_dates(start_date: datetime,
                       deadline_date: datetime,
                       end_date: datetime = None) -> None:
        """
        If the end date is not None, then the end date must be greater than the start date and the
        deadline date must be greater than the end date. If the end date is None, then the
        deadline date must be greater than the start date.

        :param start_date: The start date of the round.
        :type start_date: datetime
        :param deadline_date: The deadline date of the round.
        :type deadline_date: datetime
        :param end_date: The end date of the round, defaults to None (optional)
        :type end_date: datetime

        :raise ValidationError: If validation is not successful.
        """
        if end_date is not None and (end_date <= start_date or deadline_date < end_date):
            raise ValidationError('Round: End date out of bounds of start date and deadline.')
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
    def tasks(self) -> List[Task]:
        """
        It returns all the tasks that are associated with the round

        :return: A list of all the Task objects that are associated with the Round object.
        :rtype: QuerySet
        """
        return list(Task.objects.filter(round=self).all())

    @property
    def round_points(self) -> float:
        """
        It returns the amount of points that can be gained for completing all the tasks in the
        round.

        :return: The amount of points that can be gained for completing all the tasks in the round.
        """
        return sum(task.points for task in self.tasks)

    def __str__(self):
        return f'Round {self.pk}: {self.name}'

    def get_data(self) -> dict:
        """
        :return: The data of the round.
        :rtype: dict
        """
        return {
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'deadline_date': self.deadline_date,
            'reveal_date': self.reveal_date
        }


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


class Task(models.Model, metaclass=ReadCourseMeta):
    """
    It represents a task that user can submit a solution to. The task is judged and scored
    automatically
    """

    #: Pseudo-foreign key to package instance.
    package_instance_id = models.BigIntegerField(
        validators=[TaskManager.package_instance_exists_validator])
    #: Represents displayed task name
    task_name = models.CharField(max_length=1023)
    #: Foreign key to round, which task is assigned to.
    round = models.ForeignKey(Round, on_delete=models.CASCADE)  # noqa: A003
    #: Judging mode as choice from core.choices.TaskJudgingMode (enum-type choice)
    judging_mode = models.CharField(
        max_length=3,
        choices=TaskJudgingMode.choices,
        default=TaskJudgingMode.LIN
    )
    #: Maximum amount of points to be earned by completing this task.
    points = models.FloatField()

    #: The manager for the Task model.
    objects = TaskManager()

    class BasicAction(ModelAction):
        """
        Basic actions for Task model.
        """
        ADD = 'add', 'add_task'
        DEL = 'delete', 'delete_task'
        EDIT = 'edit', 'change_task'
        VIEW = 'view', 'view_task'

    def __str__(self):
        return (f'Task {self.pk}: {self.task_name}; '
                f'Judging mode: {TaskJudgingMode[self.judging_mode].label}; '
                f'Package: {self.package_instance}')

    def initialise_task(self) -> None:
        """
        It initialises the task by creating a new instance of the Task class, and adding all task
        sets and tests to db.

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
    def sets(self) -> List[TestSet]:
        """
        It returns all the test sets that are associated with the task

        :return: A list of all the TestSet objects that are associated with the Task object.
        """
        return list(TestSet.objects.filter(task=self).all())

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
        It returns the package instance associated with the current package instance.

        :return: A PackageInstance object.
        :rtype: PackageInstance
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

    def submits(self, user: str | int | User = None) -> List[Submit]:
        """
        It returns all the submits that are associated with the task. If user is specified,
        returns only submits of that user.

        :param user: The user who submitted the task, defaults to None (optional)
        :type user: str | int | User

        :return: A list of all the Submit objects that are associated with the Task object.
        :rtype: List[Submit]
        """
        if user is None:
            return list(Submit.objects.filter(task=self).all())
        user = ModelsRegistry.get_user(user)
        return list(Submit.objects.filter(task=self, usr=user.pk).all())

    def last_submit(self, user: str | int | User, amount=1) -> Submit | List[Submit]:
        """
        It returns the last submit of a user for a task or a list of 'amount' last submits to that
        task.

        :param user: The user who submitted the task
        :type user: str | int | User
        :param amount: The amount of submits to return, defaults to 1 (optional)
        :type amount: int

        :return: The last submit of a user for a task or a list of 'amount' last submits to that
            task.
        :rtype: Submit | List[Submit]
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

        :return: The best submit of a user for a task or list of 'amount' best submits to that task.
        :rtype: Submit | List[Submit]
        """
        user = ModelsRegistry.get_user(user)
        self.refresh_user_submits(user)
        if amount == 1:
            return Submit.objects.filter(task=self, usr=user.pk).order_by('-final_score').first()
        return Submit.objects.filter(task=self, usr=user.pk).order_by('-final_score').all()[:amount]

    @classmethod
    def check_instance(cls, pkg_instance: PackageInstance, in_every_course: bool = True) -> bool:
        """
        Check if a package instance exists in every course, optionally checking in context given
        course

        :param cls: the class of the model you're checking for
        :param pkg_instance: The PackageInstance object that you want to check for
        :type pkg_instance: PackageInstance
        :param in_every_course: If True, the package instance must be in every course.
            If False, it must be in at least one course, defaults to True
        :type in_every_course: bool (optional)

        :return: True if package instance exists in every course, False otherwise.
        :rtype: bool
        """
        if not in_every_course:
            return cls.objects.filter(package_instance_id=pkg_instance.pk).exists()

        # check in every course
        from main.models import Course

        from .routing import InCourse
        courses = Course.objects.all()
        for course in courses:
            with InCourse(course):
                if cls.objects.filter(package_instance_id=pkg_instance.pk).exists():
                    return True
        return False

    def get_data(self) -> dict:
        """
        :return: The data of the task.
        :rtype: dict
        """
        return {
            'name': self.task_name,
            'round_name': self.round.name,
            'judging_mode': self.judging_mode,
            'points': self.points,
            # 'package_instance': self.package_instance,
        }


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
            raise ValidationError(f'TestSet: Test set with short name {short_name} already exists.')

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


class TestSet(models.Model, metaclass=ReadCourseMeta):
    """
    Model groups single tests into a set of tests. Gives them a set name, and weight, used while
    calculating results for whole task.
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
        return (f'TestSet {self.pk}: Task/set: {self.task.task_name}/{self.short_name} '
                f'(w: {self.weight})')

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        It deletes the TestSet object, and all the tests that are associated with it.
        """
        for test in self.tests:
            test.delete()
        super().delete(using, keep_parents)

    @property
    def tests(self) -> List[Test]:
        """
        It returns all the tests that are associated with the test set

        :return: A list of all the tests in the test set.
        """
        return list(Test.objects.filter(test_set=self).all())


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


class Test(models.Model, metaclass=ReadCourseMeta):
    """
    Single test. Primary object to be connected with students' results.
    """

    #: Simple description what exactly is tested.
    # Corresponds to py:class:`package.package_manage.TestF`.
    short_name = models.CharField(max_length=255)
    #: Foreign key to :py:class:`TestSet`.
    test_set = models.ForeignKey(TestSet, on_delete=models.CASCADE)

    #: The manager for the Test model.
    objects = TestManager()

    def __str__(self):
        return f'Test {self.pk}: Test/set/task: ' \
               f'{self.short_name}/{self.test_set.short_name}/{self.test_set.task.task_name}'

    @property
    def associated_results(self) -> List[Result]:
        """
        Returns all results associated with this test.

        :return: QuerySet of results
        :rtype: QuerySet
        """
        return list(Result.objects.filter(test=self).all())

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
                      submit_date: datetime = None,
                      final_score: float = -1,
                      auto_send: bool = True) -> Submit:
        """
        It creates a new submit object.

        :param source_code: The path to the source code file.
        :type source_code: str | Path
        :param task: The task that you want to associate the submit with.
        :type task: int | Task
        :param user: The user that you want to associate the submit with.
        :type user: str | int | User
        :param submit_date: The date and time when the submit was created, defaults to now()
            (optional)
        :type submit_date: datetime
        :param final_score: The final score of the submit, defaults to -1 (optional)
        :type final_score: float
        :param auto_send: If True, the submit will be sent to the broker, defaults to True
            (optional)
        :type auto_send: bool

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
        if auto_send:
            new_submit.send()
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


class Submit(models.Model, metaclass=ReadCourseMeta):
    """
    Model containing single submit information. It is assigned to task and user.
    """

    #: Datetime when submit took place.
    submit_date = models.DateTimeField(auto_now_add=True)
    #: Field submitted to the task
    source_code = models.FilePathField(path=settings.SUBMITS_DIR, allow_files=True, null=True)
    #: :py:class:`Task` model, to which submit is assigned.
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    #: Pseudo-foreign key to :py:class:`main.models.User` model (user), who submitted to the task.
    usr = models.BigIntegerField(validators=[SubmitManager.user_exists_validator])
    #: Final score (as percent), gained by user's submission. Before solution check score is set
    # to ``-1``.
    final_score = models.FloatField(default=-1)

    #: The manager for the Submit model.
    objects = SubmitManager()

    class BasicAction(ModelAction):
        """
        Basic actions for Submit model.
        """
        ADD = 'add', 'add_submit'
        DEL = 'delete', 'delete_submit'
        EDIT = 'edit', 'change_submit'
        VIEW = 'view', 'view_submit'

    def send(self) -> BrokerSubmit:
        """
        It sends the submit to the broker.

        :return: None
        """
        from broker_api.models import BrokerSubmit

        return BrokerSubmit.send(ModelsRegistry.get_course(self._state.db), self.id,
                                 self.task.package_instance)

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
        return f'Submit {self.pk}: User: {self.user}; Task: {self.task.task_name}; ' \
               f"Score: {self.final_score if self.final_score > -1 else 'PENDING'}"

    @property
    def results(self) -> List[Result]:
        """
        Returns all results associated with this submit.

        :return: QuerySet of results
        :rtype: QuerySet
        """
        return list(Result.objects.filter(submit=self).all())

    @transaction.atomic
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

        # It's a cache. If the score was already calculated, it will be returned without
        # recalculating.
        if self.final_score >= 0:
            return self.final_score

        if len(self.results) < self.task.tests_amount:
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
                raise DataError(f'Submit ({self}): More test results, then test assigned to task')
            if s['SUM'] < s['MAX']:
                return -1

            # It's calculating the score of a submit, depending on judging mode.
            if judging_mode == TaskJudgingMode.LIN:
                results_aggregated[test_set]['score'] = s.get('OK', 0) / s['SUM']
            elif judging_mode == TaskJudgingMode.UNA:
                results_aggregated[test_set]['score'] = float(s.get('OK', 0) == s['SUM'])
            else:
                raise NotImplementedError(
                    f'Submit ({self}): Task {self.task.pk} has judging mode ' +
                    'which is not implemented.')

        # It's calculating the score of a submit, as weighted average of sets scores.
        final_score = 0
        final_weight = 0
        for test_set, s in results_aggregated.items():
            final_weight += (weight := TestSet.objects.filter(pk=test_set).first().weight)
            final_score += s['score'] * weight

        self.final_score = round(final_score / final_weight, 6)
        self.save()
        return self.final_score

    @staticmethod
    def format_score(score: float) -> str:
        """
        It formats the score to a string.

        :param score: The score that you want to format.
        :type score: float

        :return: The formatted score.
        :rtype: str
        """
        score = round(score * 100, 2)
        return f'{score:.2f} %' if score > -1 else 'PND'

    def get_data(self, show_user: bool = True) -> dict:
        """
        :return: The data of the submit.
        :rtype: dict
        """
        score = self.score()
        res = {
            'submit_date': self.submit_date,
            'source_code': self.source_code,
            'task': self.task.task_name,
            'final_score': self.format_score(score),
        }
        if show_user:
            res |= {'user_first_name': self.user.first_name,
                    'user_last_name': self.user.last_name}
        return res


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


class Result(models.Model, metaclass=ReadCourseMeta):
    """
    Result of single :py:class:`Test` testing.
    """

    #: :py:class:`Test` which is scored.
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    #: :py:class:`Submit` model this test is connected to.
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)
    #: Status result. Described as one of choices from :py:class:`core.choices.ResultStatus`
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
        return (f'Result {self.pk}: Set[{self.test.test_set.short_name}] '
                f'Test[{self.test.short_name}]; Stat: {ResultStatus[self.status]}')

    def delete(self, using=None, keep_parents=False, rejudge: bool = False):
        """
        It deletes the result object.
        """
        super().delete(using, keep_parents)
        if rejudge:
            self.submit.score(rejudge=True)
