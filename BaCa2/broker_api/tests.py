import cgi
from datetime import datetime, timedelta
from http import server
from threading import Thread, Lock
from typing import Any

from django.test import TestCase, Client

from BaCa2.settings import SUBMITS_DIR, BROKER_PASSWORD, BACA_PASSWORD
from broker_api.broker_communication import *
from broker_api.views import *
from course.models import Round, Task, Submit
from course.routing import InCourse
from main.models import Course, User
from package.models import PackageInstance


class DelayedAction(dict):

    INSTANCE = None

    def __new__(cls, *args, **kwargs):
        if cls.INSTANCE is None:
            cls.INSTANCE = super().__new__(cls)
        return cls.INSTANCE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.locks: dict[Any, Lock] = {}

    def set_lock(self, key):
        if key not in self.locks:
            self.locks[key] = Lock()
            self.locks[key].acquire()

    def release_lock(self, key):
        if key not in self.locks:
            self.set_lock(key)
        if self.locks[key].locked():
            self.locks[key].release()

    def put_func(self, key, func, *args, **kwargs):
        self[key] = (func, args, kwargs)
        self.release_lock(key)

    def exec_func(self, key) -> Any:
        func, args, kwargs = self[key]
        del self[key]
        return func(*args, **kwargs)

    def wait_for(self, key, timeout=5):
        tmp = self.locks[key].acquire(timeout=timeout)
        if not tmp:
            return False
        self.locks[key].release()
        del self.locks[key]
        return True

    def clear(self):
        for key in self.locks:
            if self.locks[key].locked():
                self.locks[key].release()
        self.locks.clear()
        super().clear()


def send(url, message):
    cl = Client()
    resp = cl.post(url, message, content_type='application/json')
    return resp


class DummyBrokerHandler(server.BaseHTTPRequestHandler):

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
            if content.pass_hash != make_hash(BROKER_PASSWORD, content.submit_id):
                out = BrokerToBacaError(
                    make_hash(BACA_PASSWORD, content.submit_id),
                    content.submit_id,
                    "Error"
                )
                DelayedAction.INSTANCE.put_func(content.submit_id, send,
                                                '/broker_api/error', json.dumps(out.serialize()))
            else:
                out = BrokerToBaca(
                    pass_hash=make_hash(BACA_PASSWORD, content.submit_id),
                    submit_id=content.submit_id,
                    results={}
                )
                DelayedAction.INSTANCE.put_func(content.submit_id, send,
                                                '/broker_api/result', json.dumps(out.serialize()))
        except TypeError:  # TODO
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()


class General(TestCase):
    instance = None
    course = None
    pkg_instance = None
    task = None
    user = None

    @classmethod
    def setUpClass(cls) -> None:
        DelayedAction()  # Initialize singleton

        cls.course = Course.objects.create_course(name=f'course1_{datetime.now().timestamp()}')

        cls.pkg_instance = PackageInstance.create_from_name('dosko', '1')
        cls.pkg_instance.save()

        cls.user = User.objects.create_user(password='user1',
                                            email=f'test{datetime.now().timestamp()}@test.pl')

        with InCourse(cls.course.short_name):
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
        Course.objects.delete_course(cls.course)

    def setUp(self) -> None:
        self.server = server.HTTPServer(('127.0.0.1', 8180), DummyBrokerHandler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.start()
        DelayedAction.INSTANCE.clear()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_broker_communication(self):
        src_code = SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.create_new(source_code=src_code, task=self.task, usr=self.user)
            submit.pk = datetime.now().timestamp()
            submit.save()
            submit_id = submit.pk
            DelayedAction.INSTANCE.set_lock(create_broker_submit_id(self.course.name, int(submit_id)))
            broker_submit = BrokerSubmit.send(self.course, submit_id,
                                              self.pkg_instance, broker_password=BROKER_PASSWORD)

        self.assertTrue(DelayedAction.INSTANCE.wait_for(broker_submit.broker_id, 2))
        self.assertEqual(200, DelayedAction.INSTANCE.exec_func(broker_submit.broker_id).status_code)

        broker_submit.refresh_from_db()
        self.assertTrue(broker_submit.status == BrokerSubmit.StatusEnum.SAVED)

    def test_broker_communication_error(self):
        src_code = SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.create_new(source_code=src_code, task=self.task, usr=self.user)
            submit.pk = 1
            submit.save()
            submit_id = submit.pk
            DelayedAction.INSTANCE.set_lock(create_broker_submit_id(self.course.name, int(submit_id)))
            broker_submit = BrokerSubmit.send(self.course, submit_id,
                                              self.pkg_instance, broker_password='wrong')

        self.assertTrue(DelayedAction.INSTANCE.wait_for(broker_submit.broker_id, 2))
        self.assertEqual(200, DelayedAction.INSTANCE.exec_func(broker_submit.broker_id).status_code)

        broker_submit.refresh_from_db()
        self.assertTrue(broker_submit.status == BrokerSubmit.StatusEnum.ERROR)

    def test_wrong_submit_id(self):
        ret = send('/broker_api/result', json.dumps(BrokerToBaca(
            pass_hash=make_hash(BACA_PASSWORD, 'wrong'),
            submit_id='wrong',
            results={}
        ).serialize()))
        self.assertEqual(403, ret.status_code)

        ret = send('/broker_api/error', json.dumps(BrokerToBacaError(
            pass_hash=make_hash(BACA_PASSWORD, 'wrong'),
            submit_id='wrong',
            error='error'
        ).serialize()))
        self.assertEqual(403, ret.status_code)

    def test_wrong_password(self):
        src_code = SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.create_new(source_code=src_code, task=self.task, usr=self.user)
            submit.pk = 1
            submit.save()
            submit_id = submit.pk
            DelayedAction.INSTANCE.set_lock(create_broker_submit_id(self.course.name, int(submit_id)))
            broker_submit = BrokerSubmit.send(self.course, submit_id,
                                              self.pkg_instance, broker_password='wrong')

        ret = send('/broker_api/result', json.dumps(BrokerToBaca(
            pass_hash=make_hash('wrong', broker_submit.broker_id),
            submit_id=broker_submit.broker_id,
            results={}
        ).serialize()))
        self.assertEqual(401, ret.status_code)
