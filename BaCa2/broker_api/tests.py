
from http import server
from threading import Thread
from pathlib import Path

from django.test import TestCase

from main.models import Course
from .communicate import BrokerSubmitManager
import baca2PackageManager as Bpm


class RequestHandler(server.BaseHTTPRequestHandler):

  def do_GET(self):
    request_path = self.path
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    print(self.rfile.read())


class TestOne(TestCase):

    def setUp(self) -> None:
        BrokerSubmitManager('127.0.0.1', 8001)
        self.bsm_instance = BrokerSubmitManager.instance
        self.http_server = server.HTTPServer(('127.0.0.1', 8001), RequestHandler)
        self.thread = Thread(target=self.http_server.serve_forever)
        self.thread.start()

    def tearDown(self) -> None:
        self.http_server.shutdown()
        self.thread.join()

    def test_one(self):  # TODO: finish test
        course = Course(
            name='course_one',
            short_name='c1',
            db_name='test_course'
        )
        course.save()
        package = Bpm.Package(Path('/sample'), '12121')
        print(type(course))
        self.bsm_instance.add_and_send(course, 121, package, Path('/sample'))
