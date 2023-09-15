from datetime import datetime, timedelta

import os
import json
from http import server
import cgi
from django.core.files.uploadedfile import SimpleUploadedFile
from threading import Thread
from pathlib import Path

import requests
from django.test import TestCase, Client

from BaCa2.settings import BACA_PASSWORD
from baca2PackageManager import Package
from broker_api.broker_communication import BacaToBroker, BrokerToBaca
from broker_api.models import BrokerSubmit
from course.manager import create_course, delete_course
from course.models import Round, Task, Submit
from course.routing import InCourse
from main.models import Course, User
from package.models import PackageSource, PackageInstance


class BacaApiHandler(server.BaseHTTPRequestHandler):

    def do_POST(self):
        type_, pdict = cgi.parse_header(self.headers.get('content-type'))

        if type_ != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))

        try:
            content = BacaToBroker.parse(message)
        except TypeError:  # TODO
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()


class General(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = server.HTTPServer(('127.0.0.1', 8180), BacaApiHandler)
        cls.thread = Thread(target=cls.server.serve_forever)
        cls.thread.start()

        cls.course = Course(name='course1', short_name='c1', db_name='course1_db')
        cls.course.save()
        create_course(cls.course.name)

        package = PackageSource.objects.create(name='dosko')
        cls.pkg_instance = PackageInstance.objects.create(package_source=package, commit='1')
        package.save()
        cls.pkg_instance.save()

        cls.user = User.objects.create_user(username='user1', password='user1', email='test@test.pl')

        with InCourse(cls.course.name):
            round_ = Round.objects.create(start_date=datetime.now(),
                                          deadline_date=datetime.now() + timedelta(days=1),
                                          reveal_date=datetime.now() + timedelta(days=2))
            round_.save()

            cls.task = Task.create_new(
                task_name="Liczby doskonałe",
                package_instance=cls.pkg_instance,
                round=round_,
                points=10,
            )
            cls.task.save()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

        delete_course(self.course.name)

    def test_basic(self):
        src_code = SimpleUploadedFile(name='src.cpp',
                                      content=b'#include<iostream>\nint main(){ std::cout << 1; }',
                                      content_type='text/plain')
        submit_id = None
        with InCourse(self.course.name):
            submit = Submit.create_new(source_code=src_code, task=self.task, usr=self.user)
            submit.save()
            submit_id = submit.pk

        broker_submit = BrokerSubmit.send(self.course, submit_id, self.pkg_instance)
        c = Client()
        r = c.post(path='http://127.0.0.1:8000/broker_api/result/course1/1',
                   data={
                        'course_name': 'course1',
                        'submit_id': 1,
                        'tests': [{'status': 1, 'time_real': 2.0, 'time_cpu': 1.0, 'runtime_memory': 126}]
                    },
                   content_type='application/json')
        submit.refresh_from_db()
        self.assertTrue(submit.status == submit.StatusEnum.CHECKED)
