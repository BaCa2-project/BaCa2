from django.db import models, transaction
from django.utils import timezone

import requests
import baca2PackageManager.broker_communication as brcom

from BaCa2.settings import BROKER_PASSWORD, BACA_PASSWORD, BROKER_URL
from main.models import Course
from package.models import PackageInstance
from course.routing import InCourse
from course.models import Submit

# HELP:
# package_path = package_instance.package_source.path
# commit_id = package_instance.commit


class BrokerSubmit(models.Model):

    class StatusEnum(models.IntegerChoices):
        EXPIRED = -1
        NEW = 0
        AWAITING_RESPONSE = 1
        CHECKED = 2

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    submit_id = models.BigIntegerField()
    package_instance = models.ForeignKey(PackageInstance, on_delete=models.CASCADE)

    status = models.IntegerField(StatusEnum, default=StatusEnum.NEW)
    update_date = models.DateTimeField(default=timezone.now)

    @property
    def broker_id(self):
        return brcom.create_broker_submit_id(self.course.name, int(self.submit_id))

    def hash_password(self, password: str) -> str:
        return brcom.make_hash(password, self.broker_id)

    def _send_submit(self, url: str, password: str) -> (brcom.BacaToBroker, int):
        with InCourse(self.course.name):
            tmp = Submit.objects.get(pk=self.submit_id)
            src_code = tmp.source_code.path
        message = brcom.BacaToBroker(
            pass_hash=self.hash_password(password),
            submit_id=self.broker_id,
            package_path=str(self.package_instance.path),
            commit_id=self.package_instance.commit,
            submit_path=src_code
        )
        r = requests.post(url, json=message.serialize())
        return message, r.status_code

    @classmethod
    @transaction.atomic
    def send(cls,
             course: Course,
             submit_id: int,
             package_instance: PackageInstance) -> 'BrokerSubmit':
        if cls.objects.filter(course=course, submit_id=submit_id).exists():
            raise Exception
        new_submit = cls.objects.create(
            course=course,
            submit_id=submit_id,
            package_instance=package_instance
        )
        new_submit.save()
        _, code = cls._send_submit(new_submit, BROKER_URL, BROKER_PASSWORD)
        if code != 200:
            raise ConnectionError(f'Cannot sent message to broker (error code: {code})')
        new_submit.update_status(cls.StatusEnum.AWAITING_RESPONSE)
        return new_submit

    @classmethod
    @transaction.atomic
    def handle_result(cls, broker_submit_id: str, response: brcom.BrokerToBaca) -> None:
        # Authentication
        course_name, submit_id = brcom.split_broker_submit_id(broker_submit_id)
        submit = cls.objects.get(course__name=course_name, submit_id=submit_id)
        if response.submit_id != broker_submit_id:
            raise ValueError('broker_submit_id in the url and in the json message have to match.')
        if submit is None:
            raise ValueError(f"No submit with broker_id {broker_submit_id} exists.")
        if response.pass_hash != submit.hash_password(BACA_PASSWORD):
            raise PermissionError("Wrong password.")
        submit.update_status(cls.StatusEnum.CHECKED)
        # Data processing
        ...  # TODO: implement

    @property
    def solution(self):
        with InCourse(str(self.course)):
            return Submit.objects.get(id=self.submit_id).first().source_code
        # TODO: Check if it works

    @transaction.atomic
    def update_status(self, new_status: StatusEnum):
        if new_status - 1 != self.status and new_status != self.StatusEnum.EXPIRED:
            raise ValueError(f"Attempted to change status from {self.status} to {new_status}.")
        self.status = new_status
        self.update_date = timezone.now()
        self.save()
