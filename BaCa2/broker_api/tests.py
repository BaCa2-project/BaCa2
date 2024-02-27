import cgi
from asyncio import sleep
from datetime import datetime, timedelta
from http import server
from threading import Lock, Thread
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase

from broker_api.views import *
from course.models import Result, Round, Submit, Task
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
            if content.pass_hash != make_hash(settings.BROKER_PASSWORD, content.submit_id):
                out = BrokerToBacaError(
                    make_hash(settings.BACA_PASSWORD, content.submit_id),
                    content.submit_id,
                    'Error'
                )
                DelayedAction.INSTANCE.put_func(content.submit_id, send,
                                                '/broker_api/error', json.dumps(out.serialize()))
            else:
                out = BrokerToBaca(
                    pass_hash=make_hash(settings.BACA_PASSWORD, content.submit_id),
                    submit_id=content.submit_id,
                    results={}
                )
                DelayedAction.INSTANCE.put_func(content.submit_id, send,
                                                '/broker_api/result', json.dumps(out.serialize()))
        except TypeError:
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

        cls.pkg_instance = PackageInstance.objects.create_source_and_instance('dosko', '1')
        cls.pkg_instance.save()

        cls.user = User.objects.create_user(password='user1',
                                            email=f'test{datetime.now().timestamp()}@test.pl')

        with InCourse(cls.course.short_name):
            round_ = Round.objects.create(start_date=datetime.now(),
                                          deadline_date=datetime.now() + timedelta(days=1),
                                          reveal_date=datetime.now() + timedelta(days=2))
            round_.save()

            cls.task = Task.objects.create_task(
                task_name='Liczby doskonałe',
                package_instance=cls.pkg_instance,
                round_=round_,
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
        src_code = settings.SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.objects.create_submit(source_code=src_code, task=self.task,
                                                  user=self.user, auto_send=False)
            submit.pk = datetime.now().timestamp()
            submit.save()
            submit_id = submit.pk
            DelayedAction.INSTANCE.set_lock(
                create_broker_submit_id(self.course.short_name, int(submit_id)))
            broker_submit = BrokerSubmit.send(self.course,
                                              submit_id,
                                              self.pkg_instance,
                                              broker_password=settings.BROKER_PASSWORD)

        self.assertTrue(DelayedAction.INSTANCE.wait_for(broker_submit.broker_id, 2))
        self.assertEqual(200,
                         DelayedAction.INSTANCE.exec_func(broker_submit.broker_id).status_code)

        broker_submit.refresh_from_db()
        self.assertTrue(broker_submit.status == BrokerSubmit.StatusEnum.SAVED)

    def test_broker_communication_error(self):
        src_code = settings.SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.objects.create_submit(source_code=src_code, task=self.task,
                                                  user=self.user)
            submit.pk = 1
            submit.save()
            submit_id = submit.pk
            DelayedAction.INSTANCE.set_lock(
                create_broker_submit_id(self.course.short_name, int(submit_id)))
            broker_submit = BrokerSubmit.send(self.course, submit_id,
                                              self.pkg_instance, broker_password='wrong')

        self.assertTrue(DelayedAction.INSTANCE.wait_for(broker_submit.broker_id, 2))
        self.assertEqual(200,
                         DelayedAction.INSTANCE.exec_func(broker_submit.broker_id).status_code)

        broker_submit.refresh_from_db()
        self.assertTrue(broker_submit.status == BrokerSubmit.StatusEnum.ERROR)

    def test_wrong_requests(self):
        cl = Client()
        self.assertEqual(405, cl.get('/broker_api/result').status_code)
        self.assertEqual(405, cl.get('/broker_api/error').status_code)
        self.assertEqual(415, cl.post('/broker_api/result',
                                      content_type='text/plain').status_code)
        self.assertEqual(415, cl.post('/broker_api/error',
                                      content_type='text/plain').status_code)

    def test_broker_no_communication(self):
        src_code = settings.SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.objects.create_submit(source_code=src_code, task=self.task,
                                                  user=self.user)
            submit.pk = 1
            submit.save()
            submit_id = submit.pk
            self.assertRaises(ConnectionError, BrokerSubmit.send, self.course, submit_id,
                              self.pkg_instance, broker_url='http://127.0.0.1/wrong')

        broker_submit = BrokerSubmit.objects.get(course=self.course, submit_id=submit_id)
        self.assertEqual(broker_submit.status, BrokerSubmit.StatusEnum.ERROR)

    def test_wrong_submit_id(self):
        ret = send('/broker_api/result', json.dumps(BrokerToBaca(
            pass_hash=make_hash(settings.BACA_PASSWORD, 'wrong___12'),
            submit_id='wrong___12',
            results={}
        ).serialize()))
        self.assertEqual(470, ret.status_code)

        ret = send('/broker_api/error', json.dumps(BrokerToBacaError(
            pass_hash=make_hash(settings.BACA_PASSWORD, 'wrong___12'),
            submit_id='wrong___12',
            error='error'
        ).serialize()))
        self.assertEqual(470, ret.status_code)

    def test_wrong_password(self):
        src_code = settings.SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.objects.create_submit(source_code=src_code, task=self.task,
                                                  user=self.user, auto_send=False)
            submit.pk = 1
            submit.save()
            submit_id = submit.pk
            DelayedAction.INSTANCE.set_lock(
                create_broker_submit_id(self.course.short_name, int(submit_id)))
            broker_submit = BrokerSubmit.send(self.course, submit_id,
                                              self.pkg_instance, broker_password='wrong')

        ret = send('/broker_api/result', json.dumps(BrokerToBaca(
            pass_hash=make_hash('wrong', broker_submit.broker_id),
            submit_id=broker_submit.broker_id,
            results={}
        ).serialize()))
        self.assertEqual(403, ret.status_code)

    def test_deleteErrors(self):
        for i in range(10):
            BrokerSubmit.objects.create(course=self.course,
                                        submit_id=i,
                                        package_instance=self.pkg_instance,
                                        status=BrokerSubmit.StatusEnum.ERROR,
                                        update_date=datetime.now() - timedelta(
                                            settings.BROKER_RETRY_POLICY.deletion_timeout))
        for i in range(10):
            BrokerSubmit.objects.create(course=self.course,
                                        submit_id=i,
                                        package_instance=self.pkg_instance,
                                        status=BrokerSubmit.StatusEnum.ERROR,
                                        update_date=datetime.now())
        self.assertEqual(20,
                         BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.ERROR).count())
        call_command('deleteErrors')
        self.assertEqual(10,
                         BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.ERROR).count())

    def test_markExpired(self):
        for i in range(10):
            BrokerSubmit.objects.create(course=self.course,
                                        submit_id=i,
                                        package_instance=self.pkg_instance,
                                        status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
                                        update_date=datetime.now() - timedelta(
                                            settings.BROKER_RETRY_POLICY.expiration_timeout))
        for i in range(10):
            BrokerSubmit.objects.create(course=self.course,
                                        submit_id=i,
                                        package_instance=self.pkg_instance,
                                        status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
                                        update_date=datetime.now())
        self.assertEqual(20, BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE).count())
        call_command('markExpired')
        self.assertEqual(10, BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.EXPIRED).count())

    def test_resendToBroker(self):
        for i in range(10):
            src_code = settings.SUBMITS_DIR / '1234.cpp'
            src_code = src_code.absolute()

            with InCourse(self.course.short_name):
                submit = Submit.objects.create_submit(source_code=src_code, task=self.task,
                                                      user=self.user, auto_send=False)
                submit.pk = i
                submit.save()
                submit_id = submit.pk
                BrokerSubmit.send(self.course, submit_id,
                                  self.pkg_instance, broker_password=settings.BROKER_PASSWORD)

        call_command('resendToBroker')
        self.assertEqual(10, BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE).count())
        for _ in range(settings.BROKER_RETRY_POLICY.resend_max_retries):
            BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
                                        submit_id__gte=5).update(
                status=BrokerSubmit.StatusEnum.EXPIRED)
            call_command('resendToBroker')
            self.assertEqual(10, BrokerSubmit.objects.filter(
                status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE).count())
            self.assertEqual(0, BrokerSubmit.objects.filter(
                status=BrokerSubmit.StatusEnum.EXPIRED).count())
        BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
                                    submit_id__gte=5).update(
            status=BrokerSubmit.StatusEnum.EXPIRED)
        call_command('resendToBroker')
        self.assertEqual(5, BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.ERROR).count())


class OnlineTest(TestCase):
    TIMEOUT = 60

    course = None
    pkg_instance = None
    task = None
    user = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.course = Course.objects.create_course(name=f'new course1 {datetime.now().timestamp()}')

        cls.pkg_instance = PackageInstance.objects.create_source_and_instance('dosko', '1')
        cls.pkg_instance.save()

        cls.user = User.objects.create_user(password='user1',
                                            email=f'test{datetime.now().timestamp()}@test.pl')

        with InCourse(cls.course.short_name):
            round_ = Round.objects.create_round(start_date=datetime.now(),
                                                deadline_date=datetime.now() + timedelta(days=1),
                                                reveal_date=datetime.now() + timedelta(days=2))
            round_.save()

            cls.task = Task.objects.create_task(
                task_name='Liczby doskonałe',
                package_instance=cls.pkg_instance,
                round_=round_,
                points=10,
                initialise_task=True,
            )
            cls.task.save()

    @classmethod
    def tearDownClass(cls) -> None:
        Course.objects.delete_course(cls.course)

    def test_broker_communication(self):
        src_code = settings.SUBMITS_DIR / '1234.cpp'
        src_code = src_code.absolute()

        with InCourse(self.course.short_name):
            submit = Submit.objects.create_submit(source_code=src_code,
                                                  task=self.task,
                                                  user=self.user,
                                                  auto_send=False)
            submit.save()
            broker_submit = submit.send()

        start = datetime.now()

        while all((
            broker_submit.status == BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
            datetime.now() - start < timedelta(seconds=self.TIMEOUT)
        )):
            broker_submit.refresh_from_db()
            sleep(0.1)

        self.assertTrue(broker_submit.status == BrokerSubmit.StatusEnum.SAVED)
        with InCourse(self.course.short_name):
            submit.refresh_from_db()
            self.assertTrue(submit.score == 0)
            results = Result.objects.all()
            self.assertGreater(len(results), 0)
