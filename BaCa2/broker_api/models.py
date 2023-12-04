from time import sleep

from django.db import models, transaction
from django.utils import timezone

import requests
import baca2PackageManager.broker_communication as brcom

from BaCa2.settings import BROKER_PASSWORD, BACA_PASSWORD, BROKER_URL, BROKER_RETRY
from main.models import Course
from package.models import PackageInstance
from course.routing import InCourse
from course.models import Submit, Result


# HELP:
# package_path = package_instance.package_source.path
# commit_id = package_instance.commit


class BrokerSubmit(models.Model):

    class StatusEnum(models.IntegerChoices):
        ERROR = -2
        EXPIRED = -1
        NEW = 0
        AWAITING_RESPONSE = 1
        CHECKED = 2
        SAVED = 3

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    submit_id = models.BigIntegerField()
    package_instance = models.ForeignKey(PackageInstance, on_delete=models.CASCADE)

    status = models.IntegerField(StatusEnum, default=StatusEnum.NEW)
    update_date = models.DateTimeField(default=timezone.now)
    retires = models.IntegerField(default=0)

    @property
    def broker_id(self):
        return brcom.create_broker_submit_id(self.course.name, int(self.submit_id))

    def hash_password(self, password: str) -> str:
        return brcom.make_hash(password, self.broker_id)

    def send_submit(self, url: str, password: str) -> (brcom.BacaToBroker, int):
        message = brcom.BacaToBroker(
            pass_hash=self.hash_password(password),
            submit_id=self.broker_id,
            package_path=str(self.package_instance.package_source.path),
            commit_id=self.package_instance.commit,
            submit_path=self.solution
        )
        try:
            r = requests.post(url, json=message.serialize())
        except requests.exceptions.ConnectionError:
            return message, -1
        except requests.exceptions.ChunkedEncodingError:
            return message, -2
        else:
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
        code = -100
        for _ in range(BROKER_RETRY["individual max retries"]):
            _, code = cls.send_submit(new_submit, BROKER_URL, BROKER_PASSWORD)
            if code == 200:
                break
            sleep(BROKER_RETRY["individual submit retry interval"])
        else:
            new_submit.update_status(cls.StatusEnum.ERROR)  # ???
            raise ConnectionError(f'Cannot sent message to broker (error code: {code})')
        new_submit.update_status(cls.StatusEnum.AWAITING_RESPONSE)
        return new_submit

    @classmethod
    @transaction.atomic
    def authenticate(cls, response: brcom.BrokerToBaca) -> 'BrokerSubmit':
        course_name, submit_id = brcom.split_broker_submit_id(response.submit_id)
        print(f'{course_name=}, {submit_id=}')
        broker_submit = cls.objects.filter(course__name=course_name, submit_id=submit_id).first()
        print(f'{broker_submit=}')
        if broker_submit is None:
            raise ValueError(f"No submit with broker_id {response.submit_id} exists.")
        if response.pass_hash != broker_submit.hash_password(BACA_PASSWORD):
            raise PermissionError("Wrong password.")
        return broker_submit

    @classmethod
    @transaction.atomic
    def handle_result(cls, response: brcom.BrokerToBaca) -> None:
        broker_submit = cls.authenticate(response)
        course_name, submit_id = brcom.split_broker_submit_id(response.submit_id)

        print('update status')
        broker_submit.update_status(cls.StatusEnum.CHECKED)

        print('unpack results')
        with InCourse(course_name):
            Result.unpack_results(submit_id, response)
            submit = Submit.objects.get(pk=submit_id)
            submit.score()
            print(submit)
        print('done')

        broker_submit.update_status(cls.StatusEnum.SAVED)

    @classmethod
    @transaction.atomic
    def handle_error(cls, response: brcom.BrokerToBacaError) -> None:
        broker_submit = cls.authenticate(response)
        broker_submit.update_status(cls.StatusEnum.ERROR)

    @property
    def solution(self):
        with InCourse(self.course.short_name):
            return Submit.objects.get(id=self.submit_id).source_code

    @transaction.atomic
    def update_status(self, new_status: StatusEnum):
        self.status = new_status
        self.update_date = timezone.now()
        self.save()
