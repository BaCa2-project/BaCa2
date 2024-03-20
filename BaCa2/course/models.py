from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Self

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count
from django.db.models.base import ModelBase
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from baca2PackageManager import TestF, TSet
from baca2PackageManager.broker_communication import BrokerToBaca
from baca2PackageManager.tools import bytes_from_str, bytes_to_str
from core.choices import (
    EMPTY_FINAL_STATUSES,
    HALF_EMPTY_FINAL_STATUSES,
    ModelAction,
    ResultStatus,
    SubmitType,
    TaskJudgingMode
)
from core.exceptions import DataError
from core.tools.misc import str_to_datetime
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
            elif isinstance(attr_value, models.Field):
                dest_field = result_class.__dict__.get(attr_name)
                dest_field_id = result_class.__dict__.get(f'{attr_name}_id')
                setattr(result_class, f'{attr_name}_', cls.field_decorator(dest_field))
                if dest_field_id:
                    setattr(result_class, f'{attr_name}_id_', cls.field_decorator(dest_field_id))
        return result_class

    @staticmethod
    def field_decorator(field):
        """
        Decorator used to decode origin database from object. It wraps every operation inside
        the object to be performed on meta-read database.

        :param field: Field to be wrapped
        :type field: models.Field

        :returns: Wrapped field
        """

        @property
        def field_property(self):
            if InCourse.is_defined():
                return field.__get__(self)
            with InCourse(self._state.db):
                return field.__get__(self)

        return field_property

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
                     start_date: datetime | str,
                     deadline_date: datetime | str,
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
        if isinstance(start_date, str):
            start_date = str_to_datetime(start_date)
        if isinstance(deadline_date, str):
            deadline_date = str_to_datetime(deadline_date)
        if isinstance(end_date, str):
            end_date = str_to_datetime(end_date)
        if isinstance(reveal_date, str):
            reveal_date = str_to_datetime(reveal_date)

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
    def update(self, **kwargs) -> None:
        """
        It updates the round object.

        :param kwargs: The new values for the round object.
        :type kwargs: dict
        """
        for key, value in kwargs.items():
            if key in ('start_date', 'deadline_date', 'end_date',
                       'reveal_date') and isinstance(value, str):
                value = str_to_datetime(value)
            setattr(self, key, value)
        self.validate_dates(self.start_date, self.deadline_date, self.end_date)
        self.save()

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

    def get_data(self, add_formatted_dates: bool = False) -> dict:
        """
        :param add_formatted_dates: If True, formatted dates will be added to the data, defaults to
            False (optional)
        :type add_formatted_dates: bool

        :return: The data of the round.
        :rtype: dict
        """
        from widgets.navigation import SideNav
        res = {
            'id': self.pk,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'deadline_date': self.deadline_date,
            'reveal_date': self.reveal_date,
            'normalized_name': SideNav.normalize_tab_name(self.name)
        }
        if add_formatted_dates:
            res |= {
                'f_start_date': self.start_date.strftime('%Y-%m-%d %H:%M'),
                'f_end_date': self.end_date.strftime('%Y-%m-%d %H:%M') if self.end_date else None,
                'f_deadline_date': self.deadline_date.strftime('%Y-%m-%d %H:%M'),
                'f_reveal_date': self.reveal_date.strftime(
                    '%Y-%m-%d %H:%M') if self.reveal_date else None
            }
        return res


class TaskManager(models.Manager):

    @transaction.atomic
    def create_task(self,
                    package_instance: int | PackageInstance,
                    round_: int | Round,
                    task_name: str,
                    points: float = None,
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

        if points is None:
            points = package_instance.package['points']
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
    def update_task(self,
                    task: int | Task,
                    new_package_instance: int | PackageInstance,
                    **kwargs) -> Task:
        """
        It creates a new task object from the old one, and initialises it using data from
        `PackageManager`. Old task is marked as legacy and new task is returned.

        :param task: Old task that will be updated
        :type task: int | Task
        :param new_package_instance: New package instance that will be used to update the task
        :type new_package_instance: int | PackageInstance

        :return: A new task object.
        :rtype: Task
        """

        old_task = ModelsRegistry.get_task(task)
        new_package_instance = ModelsRegistry.get_package_instance(new_package_instance)

        new_task = self.model(
            package_instance_id=new_package_instance.pk,
            task_name=kwargs.get('task_name', old_task.task_name),
            round=kwargs.get('round', old_task.round),
            judging_mode=kwargs.get('judging_mode', old_task.judging_mode),
            points=kwargs.get('points', old_task.points)
        )
        new_task.save()
        new_task.initialise_task()

        old_task.task_update = new_task
        old_task.is_legacy = True
        old_task.save()

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
    #: When task is updated, new instance is created - old submits have to be supported.
    #: Submit.update gives access to rejudging with the newest task version
    task_update = models.ForeignKey(
        to='course.Task',
        on_delete=models.SET_NULL,
        null=True,
        default=None
    )
    #: Indicates if task is legacy task, which is used only to support legacy submits
    is_legacy = models.BooleanField(default=False)

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
    def newest_update(self) -> Task:
        """
        :return: Newest update of the task
        :rtype: Task
        """
        result = self
        while result.task_update:
            result = result.task_update

        return result

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
        return ModelsRegistry.get_package_instance(self.package_instance_id)

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
            'id': self.pk,
            'name': self.task_name,
            'round_name': self.round.name,
            'judging_mode': self.judging_mode,
            'points': self.points,
            'is_legacy': self.is_legacy,
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

    @property
    def package_test_set(self) -> TSet:
        """
        :return: The TSet object that corresponds to the TestSet object.
        :rtype: TSet
        """
        return self.task.package_instance.package.sets(self.short_name)


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

    @property
    def package_test(self) -> TestF:
        """
        :return: The TestF object that corresponds to the Test object.
        :rtype: TestF
        """
        return self.test_set.package_test_set.tests(self.short_name)


class SubmitManager(models.Manager):
    @transaction.atomic
    def create_submit(self,
                      source_code: str | Path,
                      task: int | Task,
                      user: str | int | User,
                      submit_date: datetime = None,
                      final_score: float = -1,
                      auto_send: bool = True,
                      submit_type: SubmitType = SubmitType.STD,
                      submit_status: ResultStatus = ResultStatus.PND,
                      error_msg: str = None,
                      retry: int = 0,
                      **kwargs) -> Submit:
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
        :param submit_type: The type of the submit, defaults to SubmitType.STD (optional)
        :type submit_type: SubmitType
        :param submit_status: The status of the submit, defaults to None (optional)
        :type submit_status: ResultStatus
        :param error_msg: The error message of the submit, defaults to None (optional)
        :type error_msg: str
        :param retry: The number of retry, defaults to 0 (optional)
        :type retry: int

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
                                final_score=final_score,
                                submit_type=submit_type,
                                submit_status=submit_status,
                                error_msg=error_msg,
                                retries=retry)
        new_submit.save()
        if auto_send:
            new_submit.send(**kwargs)
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
    source_code = models.FilePathField(path=settings.SUBMITS_DIR,
                                       allow_files=True,
                                       null=True,
                                       max_length=2047)
    #: :py:class:`Task` model, to which submit is assigned.
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    #: Pseudo-foreign key to :py:class:`main.models.User` model (user), who submitted to the task.
    usr = models.BigIntegerField(validators=[SubmitManager.user_exists_validator])
    #: Solution type
    submit_type = models.CharField(max_length=3,
                                   choices=SubmitType.choices,
                                   default=SubmitType.STD)
    #: Status of submit (initially PND - pending)
    submit_status = models.CharField(max_length=3,
                                     choices=ResultStatus.choices,
                                     default=ResultStatus.PND)
    #: Error message, if submit ended with error
    error_msg = models.TextField(null=True, blank=True, default=None)
    #: Retries count
    retries = models.IntegerField(default=0)
    #: Final score (as percent), gained by user's submission. Before solution check score is set
    #: to ``-1``.
    final_score = models.FloatField(default=-1)

    #: The manager for the Submit model.
    objects = SubmitManager()

    class Meta:
        permissions = [
            ('view_code', _('Can view submit code')),
            ('view_compilation_logs', _('Can view submit compilation logs')),
            ('view_checker_logs', _('Can view submit checker logs')),
            ('view_student_output', _('Can view output generated by the student solution')),
            ('view_benchmark_output', _('Can view benchmark output')),
            ('view_inputs', _('Can view test inputs')),
            ('view_used_memory', _('Can view used memory')),
            ('view_used_time', _('Can view used time')),
        ]

    class BasicAction(ModelAction):
        """
        Basic actions for Submit model.
        """
        ADD = 'add', 'add_submit'
        DEL = 'delete', 'delete_submit'
        EDIT = 'edit', 'change_submit'
        VIEW = 'view', 'view_submit'

    @property
    def source_code_path(self) -> Path:
        """
        :return: Path to the source code file.
        :rtype: Path
        """
        return Path(self.source_code)

    @property
    def is_legacy(self) -> bool:
        """
        :return: True if submit is legacy, False otherwise.
        :rtype: bool
        """
        return self.task.is_legacy

    def send(self, **kwargs) -> BrokerSubmit | None:
        """
        It sends the submit to the broker. If the broker is mocked, it will run the mock broker and
        return None.

        :return: A new BrokerSubmit object or None if the broker is mocked.
        :rtype: BrokerSubmit | None
        """
        from broker_api.models import BrokerSubmit
        if settings.MOCK_BROKER:
            from broker_api.mock import BrokerMock
            mock = BrokerMock(ModelsRegistry.get_course(self._state.db), self, **kwargs)
            mock.run()
            return None

        return BrokerSubmit.send(ModelsRegistry.get_course(self._state.db),
                                 self.id,
                                 self.task.package_instance)

    def resend(self, limit_retries: int = -1) -> Submit:
        """
        It marks this submit as hidden, and creates new submit with the same data. New submit will
        be sent to broker.

        :return: A new BrokerSubmit object.
        :rtype: BrokerSubmit
        """
        if -1 < limit_retries < self.retries:
            raise ValidationError(f'Submit ({self}): Limit of retries exceeded')

        sub_type = SubmitType[self.submit_type]
        self.submit_type = SubmitType.HID
        self.save()

        new_submit = self.objects.create_submit(
            source_code=self.source_code,
            task=self.task,
            user=self.usr,
            submit_type=sub_type,
            retry=self.retries + 1
        )

        return new_submit

    def update(self) -> Self | None:
        """
        It updates the submit to the newest task update
        """
        if not self.is_legacy:
            return None

        new_task = self.task.newest_update

        new_submit = self.objects.create_submit(
            source_code=self.source_code,
            task=new_task,
            user=self.usr,
            submit_type=self.submit_type,
        )
        self.submit_type = SubmitType.HID
        return new_submit

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

    def end_with_error(self, error_type: ResultStatus, error_msg: str) -> None:
        """
        It ends the submit with an error.

        :param error_type: The type of the error.
        :type error_type: ResultStatus
        :param error_msg: The message of the error.
        :type error_msg: str
        """
        self.submit_status = error_type
        self.error_msg = error_msg

        self.final_score = 0
        self.save()

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
        submit_status = ResultStatus[self.submit_status]
        if rejudge:
            if submit_status in EMPTY_FINAL_STATUSES:
                self.final_score = 0
                self.save()
                return 0
            self.final_score = -1
            self.submit_status = ResultStatus.PND

        # It's a cache. If the score was already calculated, it will be returned without
        # recalculating.
        if self.final_score >= 0:
            return self.final_score

        if submit_status == ResultStatus.PND and len(self.results) < self.task.tests_amount:
            self.final_score = -1
            self.save()
            return -1

        if submit_status in EMPTY_FINAL_STATUSES:
            self.final_score = 0
            self.save()
            return 0

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
        worst_status = ResultStatus.PND
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

            for status in results_aggregated[test_set].keys():
                if status in ResultStatus.values:
                    status = ResultStatus[status]
                    if ResultStatus.compare(status, worst_status) > 0:
                        worst_status = status

        # It's calculating the score of a submit, as weighted average of sets scores.
        final_score = 0
        final_weight = 0
        for test_set, s in results_aggregated.items():
            final_weight += (weight := TestSet.objects.filter(pk=test_set).first().weight)
            final_score += s['score'] * weight

        self.final_score = round(final_score / final_weight, 6)
        self.submit_status = worst_status
        self.save()
        return self.final_score

    @staticmethod
    def format_score(score: float, rnd: int = 2) -> str:
        """
        It formats the score to a string.

        :param score: The score that you want to format.
        :type score: float
        :param rnd: The amount of decimal places, defaults to 2 (optional)
        :type rnd: int

        :return: The formatted score.
        :rtype: str
        """
        score = round(score * 100, rnd)
        return f'{score:.{rnd}f}' if score > -1 else '---'

    @property
    def task_score(self) -> float:
        """
        It returns the amount of points that can be gained for completing the task.

        :return: The amount of points that can be gained for completing the task.
        :rtype: float
        """
        return round(self.task.points * self.score(), 2)

    @property
    def summary_score(self) -> str:
        score = self.score()
        return f'{self.task_score} ({self.format_score(score, 1)} %)' if score > -1 else '---'

    @property
    def formatted_submit_status(self) -> str:
        """
        It returns the submit status in a formatted way.

        :return: The submit status in a formatted way.
        :rtype: str
        """
        return f'{self.submit_status} ({ResultStatus[self.submit_status].label})'

    def get_data(self,
                 show_user: bool = True,
                 add_round_task_name: bool = False,
                 add_summary_score: bool = False) -> dict:
        """
        :return: The data of the submit.
        :rtype: dict
        """
        score = self.score()
        task_score = self.task_score
        res = {
            'id': self.pk,
            'submit_date': self.submit_date,
            'source_code': self.source_code,
            'task_name': self.task.task_name,
            'task_score': task_score if score > -1 else '---',
            'final_score': self.format_score(score),
            'submit_status': self.formatted_submit_status,
            'is_legacy': self.is_legacy,
        }
        if show_user:
            res |= {'user_first_name': self.user.first_name if self.user.first_name else '---',
                    'user_last_name': self.user.last_name if self.user.last_name else '---'}
        if add_round_task_name:
            res |= {'round_task_name': f'{self.task.round.name}: {self.task.task_name}'}
        if add_summary_score:
            res |= {'summary_score': self.summary_score}
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
                logs = test_result.logs
                compile_log = logs.get('compile_log')
                checker_log = logs.get('checker_log')
                result = self.model(
                    test=test,
                    submit=submit,
                    status=test_result.status,
                    time_real=test_result.time_real,
                    time_cpu=test_result.time_cpu,
                    runtime_memory=test_result.runtime_memory,
                    compile_log=compile_log,
                    checker_log=checker_log
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
                      runtime_memory: int = None,
                      compile_log: str = None,
                      checker_log: str = None,
                      answer: str = None) -> Result:
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
        :param compile_log: The compile log of the result, defaults to None (optional)
        :type compile_log: str
        :param checker_log: The checker log of the result, defaults to None (optional)
        :type checker_log: str
        :param answer: The answer of the result, defaults to None (optional)
        :type answer: str

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
                                runtime_memory=runtime_memory,
                                compile_log=compile_log,
                                checker_log=checker_log,
                                answer=answer)
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
    #: Compile logs
    compile_log = models.TextField(null=True, default=None)
    #: Checker logs
    checker_log = models.TextField(null=True, default=None)
    #: User program's answer
    answer = models.TextField(null=True, default=None)

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

    def get_data(self,
                 include_time: bool = False,
                 include_memory: bool = False,
                 format_time: bool = True,
                 format_memory: bool = True,
                 translate_status: bool = True,
                 add_limits: bool = True,
                 add_compile_log: bool = False,
                 add_checker_log: bool = False,
                 add_user_answer: bool = False, ) -> dict:
        res = {
            'id': self.pk,
            'test_name': self.test.short_name,
            'status': self.status,
        }

        if include_time:
            res['time_real'] = self.time_real
            res['time_cpu'] = self.time_cpu
        if include_memory:
            res['runtime_memory'] = self.runtime_memory

        if include_time and format_time:
            res['f_time_real'] = f'{self.time_real:.3f} s' if self.time_real else None
            res['f_time_cpu'] = f'{self.time_cpu:.3f} s' if self.time_cpu else None
            if self.status in HALF_EMPTY_FINAL_STATUSES:
                res['f_time_real'] = self.status
                res['f_time_cpu'] = self.status
            if add_limits:
                time_limit = round(self.test.package_test['time_limit'], 3)
                res['f_time_real'] += f' / {time_limit} s'
                res['f_time_cpu'] += f' / {time_limit} s'
        if include_memory and format_memory and self.runtime_memory:
            res['f_runtime_memory'] = f'{bytes_to_str(self.runtime_memory)}'
            if self.status in HALF_EMPTY_FINAL_STATUSES:
                res['f_runtime_memory'] = self.status
            if add_limits:
                memory_limit = self.test.package_test['memory_limit']
                res['f_runtime_memory'] += f' / {bytes_to_str(bytes_from_str(memory_limit))}'
        if translate_status:
            res['f_status'] = f'{self.status} ({ResultStatus[self.status].label})'

        if add_compile_log:
            res['compile_log'] = self.compile_log
        else:
            res['compile_log'] = ''

        if add_checker_log:
            res['checker_log'] = self.checker_log
        else:
            res['checker_log'] = ''

        if add_user_answer:
            res['user_answer'] = self.answer
        else:
            res['user_answer'] = ''

        return res
