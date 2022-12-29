from pathlib import Path
from datetime import timedelta, datetime
from time import sleep
from typing import Iterable, List, Tuple, Dict
from random import choice, randint
from string import ascii_lowercase, ascii_uppercase
from unittest import TestSuite, TextTestRunner
from threading import Thread

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from BaCa2.choices import TaskJudgingMode, ResultStatus
from BaCa2.tools import random_string
from .models import *
from .routing import InCourse
from .manager import create_course, delete_course


def create_random_task(course_name: str,
                       round_task: Round,
                       task_name: str = None,
                       package_id=1,
                       judging_mode: TaskJudgingMode = None,
                       points: float = None,
                       tests=None,
                       time_offset: float = 0):
    if task_name is None:
        task_prefix = random_string(3, ascii_uppercase)
        task_name = f"{task_prefix} task {task_prefix}{random_string(15, ascii_lowercase)}"

    if judging_mode is None:
        judging_mode = choice(list(TaskJudgingMode))

    if points is None:
        points = randint(1, 20)

    if tests is None:
        tests = {}
        sets_amount = randint(1, 5)
        for i in range(sets_amount):
            set_name = f'set{i}'
            tests[set_name] = {}
            tests[set_name]['weight'] = (randint(1, 100) / 10)
            tests[set_name]['test_list'] = [f"t{j}_{random_string(3, ascii_lowercase)}" for j in range(randint(1, 10))]

    with InCourse(course_name):
        new_task = Task.objects.create(
            task_name=task_name,
            package_instance=package_id,
            round=round_task,
            judging_mode=judging_mode,
            points=points
        )
        sleep(time_offset)

        for s in tests.keys():
            new_set = TestSet.objects.create(
                task=new_task,
                short_name=s,
                weight=tests[s]['weight']
            )

            for test_name in tests[s]['test_list']:
                Test.objects.create(
                    short_name=test_name,
                    test_set=new_set
                )
                sleep(time_offset)
    return new_task


def create_random_submit(course_name: str,
                         usr,
                         parent_task: Task,
                         submit_date: datetime = timezone.now(),
                         allow_pending_status: bool = False,
                         pass_chance: float = 0.5):
    source_file = SimpleUploadedFile(f"course{course_name}_{parent_task.pk}_" +
                                     f"{submit_date.strftime('%Y_%m_%d_%H%M%S')}.txt",
                                     b"Test simple file upload.")

    allowed_statuses = list(ResultStatus)
    allowed_statuses.remove(ResultStatus.OK)
    if not allow_pending_status:
        allowed_statuses.remove(ResultStatus.PND)
    with InCourse(course_name):
        new_submit = Submit.objects.create(
            submit_date=submit_date,
            source_code=source_file,
            task=parent_task,
            usr=usr,
            final_score=-1
        )

        tests = []
        for s in parent_task.sets:
            for t in s.tests:
                tests.append(t)

        for t in tests:
            if (randint(0, 100000) / 100000) <= pass_chance:
                status = ResultStatus.OK
            else:
                status = choice(allowed_statuses)
            Result.objects.create(
                test=t,
                submit=new_submit,
                status=status
            )


def create_simple_course(course_name: str,
                         sleep_intervals: float = 0,
                         time_offset: float = 0,
                         package_instances: Iterable[int] = (1,),
                         submits: Iterable[Dict[str, int]] = None,
                         create_db: bool = True):
    if create_db:
        create_course(course_name)

    if submits is None:
        submits = ({'usr': 1, 'task': 1},)
    sleep(time_offset)
    with InCourse(course_name):
        r = Round.objects.create(
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            deadline_date=timezone.now() + timedelta(days=20),
            reveal_date=timezone.now()
        )

        sleep(sleep_intervals)
        course_tasks = []
        for t in package_instances:
            new_task = create_random_task(course_name, r, package_id=t)
            course_tasks.append(new_task)
            sleep(sleep_intervals)

        for submit in submits:
            create_random_submit(
                course_name=course_name,
                usr=submit['usr'],
                parent_task=course_tasks[submit['task'] - 1],
                pass_chance=submit.get('pass_chance', 0.5),
                allow_pending_status=submit.get('allow_pending_status', False)
            )


def submiter(course_name: str,
             usr,
             task: Task,
             submit_amount: int = 100,
             time_interval: float = 0.1,
             allow_pending_status: bool = False,
             pass_chance: float = 0.5):
    for i in range(submit_amount):
        create_random_submit(course_name, usr, task, allow_pending_status=allow_pending_status, pass_chance=pass_chance)
        sleep(time_interval)


class SimpleTestCase(TestCase):
    course_name = 'test_simple_course'

    @classmethod
    def setUpClass(cls):
        delete_course(cls.course_name)
        create_simple_course(cls.course_name, create_db=True)

    @classmethod
    def tearDownClass(cls):
        delete_course(cls.course_name)

    def test_create_simple_course(self):
        from BaCa2.settings import DATABASES
        self.assertIn(self.course_name, DATABASES.keys())

    def test_simple_access(self):
        with InCourse(self.course_name):
            tasks = Task.objects.all()
            self.assertTrue(len(tasks) > 0)

    def test_add_random_submit(self):
        with InCourse(self.course_name):
            t = Task.objects.first()
        create_random_submit(self.course_name, usr=1, parent_task=t)
        with InCourse(self.course_name):
            sub = Submit.objects.last()
            self.assertTrue(sub.task == t)
            self.assertTrue(sub.final_score == -1)

    def test_score_simple_solution(self):
        with InCourse(self.course_name):
            t = Task.objects.first()
        create_random_submit(self.course_name, usr=1, parent_task=t)

        with InCourse(self.course_name):
            sub = Submit.objects.last()
            score = sub.score()
            points = sub.task.points
            self.assertTrue(0 <= score <= points)


class MultiThreadTest(TestCase):
    course1 = 'sample_course2'
    course2 = 'sample_course3'

    @classmethod
    def setUpClass(cls):
        delete_course(cls.course1)
        delete_course(cls.course2)
        create1 = Thread(target=create_simple_course, args=(cls.course1,),
                         kwargs={
                             'time_offset': 2,
                             'sleep_intervals': 0.5,
                             'package_instances': (1, 2, 3, 4, 5),
                             'submits': [
                                 {'usr': 1, 'task': 1, 'pass_chance': 1},
                                 {'usr': 1, 'task': 2},
                                 {'usr': 2, 'task': 1},
                                 {'usr': 3, 'task': 3, 'pass_chance': 0},
                                 {'usr': 3, 'task': 1, 'pass_chance': 1},
                                 {'usr': 1, 'task': 1, 'pass_chance': 0},
                             ]
                         })
        create2 = Thread(target=create_simple_course, args=(cls.course2,),
                         kwargs={
                             'time_offset': 1,
                             'sleep_intervals': 0.3,
                             'package_instances': (1, 2, 3),
                             'submits': [
                                 {'usr': 3, 'task': 1, 'pass_chance': 1},
                                 {'usr': 3, 'task': 2},
                                 {'usr': 1, 'task': 1, 'pass_chance': 0},
                                 {'usr': 2, 'task': 2, 'pass_chance': 0},
                                 {'usr': 2, 'task': 1, 'pass_chance': 1},
                                 {'usr': 3, 'task': 1, 'pass_chance': 0},
                             ]
                         })

        create1.start()
        create2.start()
        if create1.join() and create2.join():
            pass

    @classmethod
    def tearDownClass(cls):
        delete_course(cls.course1)
        delete_course(cls.course2)

    def test_tasks_amount(self):
        with InCourse(self.course1):
            self.assertEqual(Task.objects.count(), 5)
        with InCourse(self.course2):
            self.assertEqual(Task.objects.count(), 3)

    def test_usr1_submits_amount(self):
        with InCourse(self.course1):
            self.assertEqual(Submit.objects.filter(usr=1).count(), 3)
        with InCourse(self.course2):
            self.assertEqual(Submit.objects.filter(usr=1).count(), 1)

    def test_no_pending_score(self):
        with InCourse(self.course1):
            for s in Submit.objects.all():
                self.assertNotEqual(s.score(), -1)
        with InCourse(self.course2):
            for s in Submit.objects.all():
                self.assertNotEqual(s.score(), -1)

    def test_usr1_score(self):
        self.test_no_pending_score()
        with InCourse(self.course1):
            t = Task.objects.filter(pk=1).first()
            self.assertEqual(t.best_submit(usr=1).score(), 1)

            with InCourse(self.course2):
                t = Task.objects.filter(pk=1).first()
                self.assertEqual(t.best_submit(usr=1).score(), 0)

    def test_without_InCourse_call(self):
        from BaCa2.exceptions import RoutingError
        with self.assertRaises((LookupError, RoutingError)):
            Task.objects.count()

    def two_submiters(self, submits, time_interval):
        with InCourse(self.course1):
            t1 = Task.objects.filter(pk=4).first()
            submiter1 = Thread(target=submiter, args=(self.course1, 5, t1), kwargs={
                'submit_amount': submits,
                'pass_chance': 0,
                'time_interval': time_interval
            })
        with InCourse(self.course2):
            t2 = Task.objects.filter(pk=3).first()
            submiter2 = Thread(target=submiter, args=(self.course2, 5, t2), kwargs={
                'submit_amount': submits,
                'pass_chance': 1,
                'time_interval': time_interval
            })

        submiter1.start()
        submiter2.start()

        if submiter1.join() and submiter2.join():
            with InCourse(self.course1):
                for s in Submit.objects.all():
                    self.assertEqual(s.score(), 0)
            with InCourse(self.course2):
                for s in Submit.objects.all():
                    self.assertEqual(s.score(), 1)

    def test_two_submitters_A_small(self):
        self.two_submiters(50, 0.1)

    def test_two_submitters_B_big(self):
        self.two_submiters(1000, 0)