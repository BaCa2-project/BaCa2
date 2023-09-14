
import os
import json
from http import server
import cgi
from threading import Thread
from pathlib import Path

import requests
from django.test import TestCase, Client

from main.models import Course
from course.manager import create_course, delete_course
from .models import BrokerSubmit

from package.models import PackageInstance, PackageSource
# from baca2PackageManager.broker_communication import *
from .broker_communication import *  # TODO: ^ replace with the above


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

    def setUp(self) -> None:
        self.server = server.HTTPServer(('127.0.0.1', 8180), BacaApiHandler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.start()

        self.course = Course(
            name='course1',
            short_name='c1',
            db_name='course1_db'
        )
        self.course.save()
        create_course(self.course.name)
        self.source = PackageSource(
            name='kolejka'
        )
        self.source.save()
        self.package = PackageInstance(
            package_source=self.source,
            commit=12
        )
        self.package.save()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

        delete_course(self.course.name)

    def test_basic(self):
        submit = BrokerSubmit.send(self.course, 1, self.package)
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
