from random import choice, randint

from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from parameterized import parameterized

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


def create_package_task(course, round_, pkg_name, commit, init_task: bool = True):
    if not PackageInstance.objects.filter(package_source__name=pkg_name, commit=commit).exists():
        pkg = PackageInstance.objects.create_source_and_instance(pkg_name, commit)
    else:
        pkg = PackageInstance.objects.get(package_source__name=pkg_name, commit=commit)
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
    unused_results = [r for r in possible_results]
    with InCourse(course):
        for task_set in submit.task.sets:
            for test in task_set.tests:
                if unused_results:
                    result = create_test_result(submit, test, choice(unused_results))
                    unused_results.remove(result.status)
                else:
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
    pkg = None

    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create_course(
            name='Test Course',
            short_name='TC1',
        )
        cls.pkg = PackageInstance.objects.create_source_and_instance('dosko', '1')

    @classmethod
    def tearDownClass(cls):
        Course.objects.delete_course(cls.course)
        pkg_src = cls.pkg.package_source
        cls.pkg.delete()
        pkg_src.delete()

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
            self.assertTrue(round1.is_open)
            round1.delete()

    def generic_round_with_2_tasks(self,
                                   init_tasks=False) -> Round:
        round_ = Round.objects.create_round(
            start_date=timezone.now() - timedelta(days=1),
            deadline_date=timezone.now() + timedelta(days=1),
        )
        Task.objects.create_task(
            task_name='Test Task 1',
            package_instance=self.pkg,
            round_=round_,
            points=5,
            initialise_task=init_tasks
        )
        Task.objects.create_task(
            task_name='Test Task 2',
            package_instance=self.pkg,
            round_=round_,
            points=5,
            initialise_task=init_tasks
        )
        return round_

    def test_06_tasks_listing(self):
        with InCourse(self.course):
            round1 = self.generic_round_with_2_tasks()
            self.assertEqual(round1.tasks.count(), 2)
            round1.delete()

    def test_07_round_points(self):
        with InCourse(self.course):
            round1 = self.generic_round_with_2_tasks()
            self.assertEqual(round1.round_points, 10)
            round1.delete()


class TaskTestMain(TestCase):
    course = None
    round1 = None
    round2 = None

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
        create_package_task(self.course, self.round1, 'dosko', '1', init_task=False)
        with InCourse(self.course):
            self.assertEqual(Task.objects.count(), 1)
            self.assertEqual(Task.objects.get(
                task_name='Test task with package').points, 10)

    def test_02_create_package_task_no_init(self):
        """
        Creates a task with a package and then checks access to package instance
        """
        task = create_package_task(self.course, self.round1, 'dosko', '1', init_task=False)
        with InCourse(self.course):
            self.assertEqual(Task.objects.count(), 1)
            self.assertEqual(task.package_instance.package_source.name, 'dosko')
            self.assertEqual(task.package_instance.commit, '1')

    def test_03_create_package_task_init(self):
        task = create_package_task(self.course, self.round1, 'dosko', '1', init_task=True)
        with InCourse(self.course):
            pkg = task.package_instance.package
            self.assertEqual(pkg['title'], 'Liczby Doskonałe')
            self.assertEqual(len(task.sets), 4)
            self.assertEqual(pkg.sets('set0')['name'], 'set0')
            set0 = task.sets.filter(short_name='set0').first()
            self.assertEqual(len(set0.tests), 2)
            tests = [t.short_name for t in set0.tests]
            self.assertIn('dosko0a', tests)
            self.assertIn('dosko0b', tests)

    def test_04_init_task_delete_without_results(self):
        try:
            self.test_03_create_package_task_init()
        except AssertionError:
            self.skipTest('Creation of package test is not working properly')
        self.tearDown()

        task = create_package_task(self.course, self.round2, 'dosko', '1', init_task=True)
        with InCourse(self.course):
            Task.objects.delete_task(task)
            self.assertEqual(Task.objects.count(), 0, f'Tasks: {Task.objects.all()}')
            self.assertEqual(TestSet.objects.count(), 0, f'TestSets: {TestSet.objects.all()}')
            self.assertEqual(Test.objects.count(), 0, f'Tests: {Test.objects.all()}')


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
        cls.task1 = create_package_task(cls.course, cls.round_, 'dosko', '1', init_task=True)
        cls.task2 = create_package_task(cls.course, cls.round_, 'dosko', '1', init_task=True)
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
            Submit.objects.all().delete()

    def test_01_add_result(self):
        submit = create_submit(self.course, self.task1, self.user, '1234.cpp')
        create_task_results(self.course, submit)
        with InCourse(self.course):
            self.assertEqual(Test.objects.filter(test_set__task=self.task1).count(),
                             Result.objects.filter(submit__task=self.task1).count())
            self.assertTrue(all(
                [r.status == ResultStatus.OK for r in submit.results]
            ))

    @parameterized.expand([
        ('all ok', (ResultStatus.OK,)),
        ('ANS and TLE', (ResultStatus.ANS, ResultStatus.TLE,))])
    def test_02_check_scoring(self, name, possible_results):
        submit = create_submit(self.course, self.task1, self.user, '1234.cpp')
        create_task_results(self.course, submit, possible_results)
        with InCourse(self.course):
            if name == 'all ok':
                self.assertEqual(submit.score(), 1.0)
            else:
                self.assertEqual(submit.score(), 0)

    @parameterized.expand([
        ('best submit',),
        ('last submit',),
    ])
    def test_03_check_scoring_with_multiple_submits(self, name):
        submit1 = create_submit(self.course, self.task1, self.user, '1234.cpp')
        submit2 = create_submit(self.course, self.task1, self.user, '1234.cpp')
        create_task_results(self.course, submit1)
        create_task_results(self.course, submit2, (ResultStatus.ANS,))
        with InCourse(self.course):
            if name == 'best submit':
                best_submit = self.task1.best_submit(self.user)
                self.assertEqual(best_submit.score(), 1.0)
                self.assertEqual(best_submit, submit1)
            if name == 'last submit':
                last_submit = self.task1.last_submit(self.user)
                self.assertEqual(last_submit.score(), 0)
                self.assertEqual(last_submit, submit2)

    @parameterized.expand([
        ('best submit', 10),
        ('last submit', 10),
        ('best submit', 100),
        ('last submit', 100),
        ('best submit', 500),
        ('last submit', 500),
    ])
    def test_04_multiple_submits(self, name, submits_amount):
        best_s = randint(0, submits_amount - 2)
        for i in range(submits_amount):
            submit = create_submit(self.course, self.task1, self.user, '1234.cpp')
            if i == best_s:
                create_task_results(self.course, submit)
            else:
                create_task_results(self.course, submit,
                                    (ResultStatus.OK, ResultStatus.ANS, ResultStatus.TLE))
        with InCourse(self.course):
            if name == 'best submit':
                best_submit = self.task1.best_submit(self.user)
                self.assertEqual(best_submit.score(), 1.0)
            if name == 'last submit':
                last_submit = self.task1.last_submit(self.user)
                self.assertLess(last_submit.score(), 1)
                self.assertGreater(last_submit.score(), 0)

    