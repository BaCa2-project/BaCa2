from random import choice

import unittest

from django.core.exceptions import ValidationError
from pathlib import Path
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from BaCa2.choices import ResultStatus
from package.models import PackageInstance
from .models import *
from main.models import Course, User
from .routing import InCourse, OptionalInCourse


def create_rounds(course, amount):
    with InCourse(course):
        rounds = []
        for i in range(amount):
            new_round = Round.objects.create_round(
                start_date=timezone.now() - timedelta(days=1),
                deadline_date=timezone.now() + timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
            )
            new_round.save()
            rounds.append(new_round)
    return rounds


def create_tasks(round_, amount):
    with InCourse(round_.course):
        tasks = []
        for i in range(amount):
            new_task = Task.objects.create(
                package_instance_id=i,
                task_name=f'Test Task {i}',
                round=round_,
                points=10,
            )
            new_task.save()
            tasks.append(new_task)
    return tasks


def create_package_task(course, round_, pkg_name, commit, init_task: bool = True):
    if not PackageInstance.objects.filter(package_source__name=pkg_name, commit=commit).exists():
        pkg = PackageInstance.objects.create_source_and_instance(pkg_name, commit)
    else:
        pkg = PackageInstance.objects.get(package_name=pkg_name, commit=commit)
    with InCourse(course):
        task = Task.objects.create_task(
            package_instance=pkg,
            round_=round_,
            task_name="Test task with package",
            points=10,
            initialise_task=init_task,
        )
        task.save()
    return task


def create_test_result(submit, test, status, course=None):
    with OptionalInCourse(course):
        result = Result.objects.create_result(
            submit=submit,
            test=test,
            status=status,
            time_real=0.5,
            time_cpu=0.3,
            runtime_memory=123,
        )
        result.save()
    return result


def create_task_results(course, submit, possible_results=(ResultStatus.OK,)):
    with InCourse(course):
        for task_set in submit.task.sets:
            for test in task_set.tests:
                create_test_result(submit, test, choice(possible_results))


def create_submit(course, task, user, src_code):
    with InCourse(course):
        submit = Submit.objects.create_submit(
            source_code=src_code,
            task=task,
            user=user,
        )
        submit.save()
    return submit


class RoundTest(TestCase):
    course = None

    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create_course(
            name='Test Course',
            short_name='TC1',
        )

    @classmethod
    def tearDownClass(cls):
        Course.objects.delete_course(cls.course)

    def tearDown(self):
        with InCourse(self.course):
            Round.objects.all().delete()

    def test_01_create_round(self):
        """
        Test creating a round
        """
        with InCourse(self.course):
            round1 = Round.objects.create_round(
                start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
                deadline_date=datetime(2020, 1, 2, tzinfo=timezone.utc),
            )
            round2 = Round.objects.create_round(
                start_date=datetime(2020, 1, 3, tzinfo=timezone.utc),
                deadline_date=datetime(2020, 1, 5, tzinfo=timezone.utc),
                end_date=datetime(2020, 1, 4, tzinfo=timezone.utc),
                reveal_date=datetime(2020, 1, 6, tzinfo=timezone.utc),
            )
            round1.save()
            round2.save()

        with InCourse(self.course):
            self.assertEqual(Round.objects.count(), 2)
            round_res = Round.objects.get(
                start_date=datetime(2020, 1, 3, tzinfo=timezone.utc))
            self.assertEqual(round_res.end_date,
                             datetime(2020, 1, 4, tzinfo=timezone.utc))
            self.assertEqual(round_res.reveal_date,
                             datetime(2020, 1, 6, tzinfo=timezone.utc))

    def test_02_validate_round(self):
        with InCourse(self.course):
            with self.assertRaises(ValidationError):
                Round.objects.create_round(
                    start_date=datetime(2020, 1, 2, tzinfo=timezone.utc),
                    deadline_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
                )

    def test_03_round_delete(self):
        round_nb = 0
        with InCourse(self.course):
            new_round = Round.objects.create_round(
                start_date=timezone.now() - timedelta(days=1),
                deadline_date=timezone.now() + timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
            )
            new_round.save()
            round_nb = new_round.pk
            self.assertEqual(Round.objects.all().first(), new_round)
        with InCourse(self.course):
            Round.objects.delete_round(round_nb)
            self.assertEqual(Round.objects.count(), 0)

    def test_04_round_advanced_delete(self):
        with InCourse(self.course):
            round1 = Round.objects.create_round(
                start_date=datetime(2021, 1, 1, tzinfo=timezone.utc),
                deadline_date=datetime(2021, 1, 2, tzinfo=timezone.utc),
            )

            create_package_task(self.course, round1, 'dosko', '1', init_task=False)

            self.assertEqual(Task.objects.count(), 1)
            self.assertEqual(Task.objects.first().task_name, "Test task with package")

            round1.delete()
            self.assertEqual(Task.objects.count(), 0)

    def test_05_is_open(self):
        with InCourse(self.course):
            round1 = Round.objects.create_round(
                start_date=timezone.now() - timedelta(days=1),
                deadline_date=timezone.now() + timedelta(days=1),
            )
            self.assertTrue(round1.is_open())
            round1.delete()

    def test_06_tasks_listing(self):
        with InCourse(self.course):
            round1 = Round.objects.create_round(
                start_date=timezone.now() - timedelta(days=1),
                deadline_date=timezone.now() + timedelta(days=1),
            )
            Task.objects.create_task(
                name='Test Task',
                description='Test Description',
                max_points=5,
                round=round1,
            )
            Task.objects.create_task(
                name='Test Task 2',
                description='Test Description 2',
                max_points=5,
                round=round1,
            )
            self.assertEqual(round1.tasks.count(), 2)
            round1.delete()

    def test_07_round_points(self):
        with InCourse(self.course):
            round1 = Round.objects.create_round(
                start_date=timezone.now() - timedelta(days=1),
                deadline_date=timezone.now() + timedelta(days=1),
            )
            Task.objects.create_task(
                name='Test Task',
                description='Test Description',
                max_points=5,
                round=round1,
            )
            Task.objects.create_task(
                name='Test Task 2',
                description='Test Description 2',
                max_points=5,
                round=round1,
            )
            self.assertEqual(round1.max_points, 10)
            round1.delete()


class TaskTestMain(TestCase):
    course = None
    round1 = None
    round2 = None
    creator_03_works = False

    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create_course(
            name='Test Course',
            short_name='TC2',
        )
        cls.round1 = create_rounds(cls.course, 1)[0]
        cls.round2 = create_rounds(cls.course, 1)[0]

    @classmethod
    def tearDownClass(cls):
        Course.objects.delete_course(cls.course)

    def tearDown(self):
        with InCourse(self.course):
            Task.objects.all().delete()

    def test_01_create_and_delete_task(self):
        task = create_tasks(self.round1, 1)[0]
        with InCourse(self.course):
            self.assertEqual(Task.objects.count(), 1)
            self.assertEqual(Task.objects.get(
                name='Test Task 0').first().max_points, 10)

    def test_02_create_package_task_no_init(self):
        """
        Creates a task with a package and then checks access to package instance
        """
        task = create_package_task(self.round1, 'dosko', '1', init_task=False)
        with InCourse(self.course):
            self.assertEqual(Task.objects.count(), 1)
            self.assertEqual(task.package_instance.package_source.name, 'dosko')
            self.assertEqual(task.package_instance.commit, '1')

    def test_03_create_package_task_init(self):
        task = create_package_task(self.round1, 'dosko', '1', init_task=True)
        with InCourse(self.course):
            pkg = task.package_instance.package
            self.assertEqual(pkg['name'], 'Liczby Doskonałe')
            self.assertEqual(len(task.sets), 4)
            self.assertEqual(pkg.sets('set0')['name'], 'set0')
            set0 = task.sets.filter(short_name='set0').first()
            self.assertEqual(len(set0.tests), 2)
            tests = [t.short_name for t in set0.tests]
            self.assertIn('dosko0a', tests)
            self.assertIn('dosko0b', tests)
        self.creator_03_works = True

    def test_04_init_task_delete_without_results(self):
        if not self.creator_03_works:
            self.skipTest('Creation of package test is not working properly')

        task = create_package_task(self.round2, 'dosko', '1', init_task=True)
        with InCourse(self.course):
            Task.objects.delete_task(task)
            self.assertEqual(Task.objects.count(), 0)
            self.assertEqual(TestSet.objects.count(), 0)
            self.assertEqual(Test.objects.count(), 0)


@unittest.skipUnless(TaskTestMain.creator_03_works,
                     'Creation of package test is not working properly')
class TestTaskWithResults(TestCase):
    course = None
    round_ = None
    user = None

    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create_course(
            name='Test Course',
            short_name='TC3',
        )
        cls.round_ = create_rounds(cls.course, 1)[0]
        cls.task1 = create_package_task(cls.round_, 'dosko', '1', init_task=True)
        cls.task2 = create_package_task(cls.round_, 'dosko', '1', init_task=True)
        cls.user = User.objects.create_user(
            email='test@test.com',
            password='test',
        )

    @classmethod
    def tearDownClass(cls):
        Course.objects.delete_course(cls.course)
        cls.user.delete()

    def tearDown(self):
        with InCourse(self.course):
            Result.objects.all().delete()

    def test_01_add_result(self):
        submit = create_submit(self.course, self.task1, self.user, '1234.cpp')
        create_task_results(self.course, submit)
        with InCourse(self.course):
            self.assertCountEqual(Test.objects.get(task=self.task1).all(),
                                  Result.objects.get(task=self.task1).all())
            self.assertTrue(all(
                [r.status == ResultStatus.OK for r in submit.results]
            ))
