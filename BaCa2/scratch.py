import sys
import os

import django

# sys.path.insert(0, os.path.abspath('.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'BaCa2.settings'
django.setup()

from time import sleep

from datetime import datetime, timedelta

from broker_api.models import BrokerSubmit
from course.manager import create_course, delete_course
from course.models import Round, Task, Submit
from course.routing import InCourse
from main.models import Course, User
from package.models import PackageInstance
from BaCa2.settings import SUBMITS_DIR


course = Course(name='course1', short_name='c1', db_name='course1_db')
course.save()
create_course(course.name)

pkg_instance = PackageInstance.create_from_name('dosko', '1')
pkg_instance.save()

user = User.objects.create_user(username=f'user1_{datetime.now().timestamp()}',
                                password='user1',
                                email=f'test{datetime.now().timestamp()}@test.pl')

with InCourse(course.name):
    round = Round.objects.create(start_date=datetime.now(),
                                 deadline_date=datetime.now() + timedelta(days=1),
                                 reveal_date=datetime.now() + timedelta(days=2))
    round.save()

    task = Task.create_new(
        task_name="Liczby doskonałe",
        package_instance=pkg_instance,
        round=round,
        points=10,
    )
    task.save()

# src_code = SUBMITS_DIR / '1234.cpp'
src_code = SUBMITS_DIR / 'dosko.py'
src_code = src_code.absolute()

submit_id = None
with InCourse(course.name):
    submit = Submit.create_new(source_code=src_code, task=task, usr=user)
    submit.pk = datetime.now().timestamp()
    submit.save()
    submit_id = submit.pk

broker_submit = BrokerSubmit.send(course, submit_id, pkg_instance)

while broker_submit.status != BrokerSubmit.StatusEnum.SAVED:
    sleep(1)
    broker_submit.refresh_from_db()

delete_course('course1')
