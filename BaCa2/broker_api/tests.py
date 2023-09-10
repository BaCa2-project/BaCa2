
import os
import json
from http import server
import cgi
from threading import Thread
from pathlib import Path

import requests
from django.test import TestCase, Client

from baca2PackageManager import Package
from main.models import Course

from .message import *
from .communicate import BrokerSubmitManager


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
            content = BacaToBroker(**message)
        except TypeError:  # TODO
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()


class General(TestCase):

    def setUp(self) -> None:
        self.instance = BrokerSubmitManager('http://127.0.0.1:8180/')
        self.server = server.HTTPServer(('127.0.0.1', 8180), BacaApiHandler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_basic(self):
        course = Course(
            name='course1',
            short_name='c1',
            db_name='course1_db'
        )
        course.save()
        package = Package(
            path=Path(os.path.dirname(__file__) + '/test/kolejka'),
            commit='commit1'
        )
        submit = self.instance.send(course, 1, package, 'sample/path')
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
