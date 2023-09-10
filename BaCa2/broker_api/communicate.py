from typing import Optional
from pathlib import Path
from dataclasses import asdict
from threading import Lock

import requests

import baca2PackageManager as Bpm
from main.models import Course

from .models import BrokerSubmit
from .message import BacaToBroker, BrokerToBaca


class BrokerSubmitManager:
    # TODO: improve data integrity fail saves (self.lock)

    instance: Optional['BrokerSubmitManager'] = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, broker_url: str, timeout: float = 30):
        self.broker_url = broker_url
        self.timeout = timeout
        self.lock = Lock()

    def _send_submit(self, submit: BrokerSubmit) -> int:
        message = BacaToBroker(
            course_name=submit.course.name,
            submit_id=submit.submit_id,
            package_path=submit.package_path,
            solution_path=submit.solution_path
        )
        r = requests.post(self.broker_url, json=asdict(message))
        return r.status_code

    def send(self,
             course: Course,
             submit_id: int,
             package: Bpm.Package,
             solution_path: Path) -> BrokerSubmit:
        if BrokerSubmit.objects.filter(course=course, submit_id=submit_id).exists():
            raise Exception
        new_submit = BrokerSubmit.objects.create(
            course=course,
            submit_id=submit_id,
            package_path=str(package.commit_path),
            solution_path=str(solution_path),
            status=BrokerSubmit.StatusEnum.NEW
        )
        new_submit.save()
        with self.lock:
            success = self._send_submit(new_submit)
            if success != 200:
                raise Exception  # TODO
            new_submit.update_status(BrokerSubmit.StatusEnum.AWAITING_RESPONSE)
            new_submit.save()
        return new_submit

    def handle_result(self, course: str, submit_id: int, response: BrokerToBaca):
        with self.lock:
            submit = BrokerSubmit.objects.get(course__name=course, submit_id=submit_id)
            if submit is None:
                raise Exception  # TODO
            submit.update_status(BrokerSubmit.StatusEnum.CHECKED)
        ...  # TODO

    @staticmethod
    def handle_status(course: str, submit_id: int, status) -> None:
        ...
