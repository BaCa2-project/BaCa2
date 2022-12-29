from pathlib import Path
from datetime import timedelta, datetime
from time import sleep
from typing import Iterable, List, Tuple, Dict
from random import choice, randint
from string import ascii_lowercase, ascii_uppercase
from unittest import TestSuite, TextTestRunner

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



# def simple_test_suite():
#     suite = TestSuite()
#     suite.addTest(SimpleTestCase('test_create_simple_course'))
#     suite.addTest(SimpleTestCase('test_simple_access'))
#     suite.addTest(SimpleTestCase('test_add_random_submit'))
#     suite.addTest(SimpleTestCase('test_score_simple_solution'))
#     suite.addTest(SimpleTestCase('test_delete_simple_course'))
#     return suite

#
# if __name__ == '__main__':
#     runner = TextTestRunner()
#     runner.run(simple_test_suite())
