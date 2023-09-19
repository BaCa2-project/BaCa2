from datetime import datetime, timedelta

import json
from http import server
import cgi
from time import sleep

from django.core.files.uploadedfile import SimpleUploadedFile
from threading import Thread

from django.test import TestCase, Client

from BaCa2.settings import BACA_PASSWORD
from broker_api.broker_communication import BacaToBroker, BrokerToBaca
from broker_api.models import BrokerSubmit
from course.manager import create_course, delete_course
from course.models import Round, Task, Submit
from course.routing import InCourse
from main.models import Course, User
from package.models import PackageSource, PackageInstance
from BaCa2.settings import SUBMITS_DIR


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
    instance = None
    server = None
    thread = None
    course = None
    pkg_instance = None
    task = None
    user = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.course = Course(name='course1', short_name='c1', db_name='course1_db')
        cls.course.save()
        create_course(cls.course.name)

        cls.pkg_instance = PackageInstance.create_from_name('dosko', '1')
        cls.pkg_instance.save()

        cls.user = User.objects.create_user(username=f'user1_{datetime.now().timestamp()}',
                                            password='user1',
                                            email=f'test{datetime.now().timestamp()}@test.pl')

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
        delete_course(cls.course.name)

    def tearDown(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.server = None
            self.thread = None

    # def test_basic(self):
    #     self.server = server.HTTPServer(('127.0.0.1', 8180), BacaApiHandler)
    #     self.thread = Thread(target=self.server.serve_forever)
    #     self.thread.start()
    #
    #     src_code = SUBMITS_DIR / '1234.cpp'
    #
    #     submit_id = None
    #     with InCourse(self.course.name):
    #         submit = Submit.create_new(source_code=src_code, task=self.task, usr=self.user)
    #         submit.save()
    #         submit_id = submit.pk
    #
    #     broker_submit = BrokerSubmit.send(self.course, submit_id, self.pkg_instance)
    #     c = Client()
    #     data = BrokerToBaca(
    #         pass_hash=broker_submit.hash_password(BACA_PASSWORD),
    #         submit_id=broker_submit.broker_id,
    #         results={}
    #     )
    #     r = c.post(path=f'http://127.0.0.1:8000/broker_api/result/{broker_submit.broker_id}',
    #                data=data.serialize(),
    #                content_type='application/json')
    #     broker_submit.refresh_from_db()
    #     self.assertTrue(broker_submit.status == broker_submit.StatusEnum.CHECKED)

    def test_broker_communication(self):
        # this test requires running broker server on localhost:8180

        src_code = SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        submit_id = None
        with InCourse(self.course.name):
            submit = Submit.create_new(source_code=src_code, task=self.task, usr=self.user)
            submit.pk = datetime.now().timestamp()
            submit.save()
            submit_id = submit.pk

        broker_submit = BrokerSubmit.send(self.course, submit_id, self.pkg_instance)

        while broker_submit.status != BrokerSubmit.StatusEnum.SAVED:
            sleep(1)
            broker_submit.refresh_from_db()
