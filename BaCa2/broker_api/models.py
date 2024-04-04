import logging
from time import sleep

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

import baca2PackageManager.broker_communication as brcom
import requests
from core.choices import ResultStatus
from course.models import Result, Submit
from course.routing import InCourse
from main.models import Course
from package.models import PackageInstance
from util.models_registry import ModelsRegistry

logger = logging.getLogger(__name__)


class BrokerSubmitManager(models.Manager):
    ...
    # TODO: move class methods from BrokerSubmit to BrokerSubmitManager


class BrokerSubmit(models.Model):
    """Model for storing information about submits sent to broker."""

    class StatusEnum(models.IntegerChoices):
        """Enum for submit status."""
        ERROR = -2  # Error while sending or receiving submit
        EXPIRED = -1  # Submit was not checked in time
        NEW = 0  # Submit was created
        PROCESSING = 1  # Submit is being processed
        AWAITING_RESPONSE = 2  # Submit was sent to broker and is awaiting response
        CHECKED = 3  # Submit was checked and results are being saved
        SAVED = 4  # Results were saved

    #: course foreign key
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    #: package instance foreign key
    package_instance = models.ForeignKey(PackageInstance, on_delete=models.CASCADE)
    #: submit id
    submit_id = models.BigIntegerField()

    #: status of this submit
    status = models.IntegerField(StatusEnum, default=StatusEnum.NEW)
    #: date of last status update
    update_date = models.DateTimeField(default=timezone.now)
    #: amount of times this submit was resent to broker
    retry_amount = models.IntegerField(default=0)

    def __repr__(self):
        return f'BrokerSubmit({self.broker_id})'

    @property
    def broker_id(self):
        """
        Returns broker_id of this submit.

        :return: broker_id of this submit
        :rtype: str
        """
        return brcom.create_broker_submit_id(self.course.short_name, int(self.submit_id))

    @property
    def submit(self) -> Submit:
        """
        :return: Submit object from course database
        :rtype: Submit
        """
        return self.course.get_submit(self.submit_id)

    def hash_password(self, password: str) -> str:
        """
        Hashes password with broker_id as salt.

        :param password: password to hash
        :type password: str

        :return: hashed password
        :rtype: str
        """
        return brcom.make_hash(password, self.broker_id)

    def send_submit(self, url: str, password: str) -> tuple[brcom.BacaToBroker, int]:
        """
        Sends submit to broker.

        :param url: url of broker
        :type url: str
        :param password: password for broker
        :type password: str

        :return: tuple (message, status_code) where message is message sent to broker and
            status_code is an HTTP status code or a negative number if an error occurred
        :rtype: tuple[brcom.BacaToBroker, int]
        """
        message = brcom.BacaToBroker(
            pass_hash=self.hash_password(password),
            submit_id=self.broker_id,
            package_path=str(self.package_instance.package_source.path),
            commit_id=self.package_instance.commit,
            submit_path=self.solution
        )
        try:
            r = requests.post(url, headers={'content-type': 'application/json'},
                              data=message.model_dump_json())
        except requests.exceptions.ConnectionError:
            return message, -1
        except requests.exceptions.ChunkedEncodingError:
            return message, -2
        else:
            return message, r.status_code

    @classmethod
    def send(cls,
             course: Course,
             submit_id: int,
             package_instance: PackageInstance,
             broker_url: str = settings.BROKER_URL,
             broker_password: str = settings.BROKER_PASSWORD) -> 'BrokerSubmit':
        """
        Creates new submit and sends it to broker.

        :param course: course of this submit
        :type course: Course
        :param submit_id: id of this submit
        :type submit_id: int
        :param package_instance: package instance of this submit
        :type package_instance: PackageInstance
        :param broker_url: url of broker
        :type broker_url: str
        :param broker_password: password for broker
        :type broker_password: str

        :return: new submit
        :rtype: BrokerSubmit

        :raises ConnectionError: if submit cannot be sent to broker
        """
        if cls.objects.filter(course=course, submit_id=submit_id).exists():
            raise ValueError(f'Submit with id {submit_id} already exists.')
        new_submit = cls.objects.create(
            course=course,
            submit_id=submit_id,
            package_instance=package_instance
        )
        new_submit.save()
        new_submit.update_status(cls.StatusEnum.PROCESSING)
        code = -100
        for _ in range(settings.BROKER_RETRY_POLICY.individual_max_retries):
            _, code = cls.send_submit(new_submit, broker_url, broker_password)
            if code == 200:
                break
            sleep(settings.BROKER_RETRY_POLICY.individual_submit_retry_interval)
        else:
            new_submit.update_status(cls.StatusEnum.ERROR)
            new_submit.submit.end_with_error(ResultStatus.INT,
                                             f'Cannot sent message to broker (error code: {code})')
            raise ConnectionError(f'Cannot sent message to broker (error code: {code})')
        new_submit.update_status(cls.StatusEnum.AWAITING_RESPONSE)
        return new_submit

    def resend(self,
               broker_url: str = settings.BROKER_URL,
               broker_password: str = settings.BROKER_PASSWORD):
        """
        Resends this submit to broker.

        :param broker_url: url of broker
        :type broker_url: str
        :param broker_password: password for broker
        :type broker_password: str
        """
        self.status = self.StatusEnum.PROCESSING
        for _ in range(settings.BROKER_RETRY_POLICY.individual_max_retries):
            _, code = self.send_submit(broker_url, broker_password)
            if code == 200:
                self.retry_amount += 1
                self.update_status(self.StatusEnum.AWAITING_RESPONSE)
                break
            sleep(settings.BROKER_RETRY_POLICY.individual_submit_retry_interval)
        else:
            self.submit.end_with_error(ResultStatus.INT, 'Cannot sent message to broker')
            self.update_status(self.StatusEnum.ERROR)

    @classmethod
    def authenticate(cls, response: brcom.BrokerToBaca) -> 'BrokerSubmit':
        """
        Authenticates response from broker and returns the corresponding submit.

        :param response: response from broker
        :type response: brcom.BrokerToBaca

        :return: submit corresponding to response
        :rtype: BrokerSubmit

        :raises ValueError: if no submit with broker_id from response exists
        :raises PermissionError: if password in response is wrong
        """
        course_name, submit_id = brcom.split_broker_submit_id(response.submit_id)
        broker_submit = cls.objects.filter(course__short_name=course_name,
                                           submit_id=submit_id).first()
        if broker_submit is None:
            raise ValueError(f'No submit with broker_id {response.submit_id} exists.')
        if response.pass_hash != broker_submit.hash_password(settings.BACA_PASSWORD):
            raise PermissionError('Wrong password.')
        return broker_submit

    @classmethod
    def handle_result(cls, response: brcom.BrokerToBaca):
        """
        Handles result from broker and saves it to database.

        :param response: response from broker
        :type response: brcom.BrokerToBaca
        """
        broker_submit = cls.authenticate(response)
        course_name, submit_id = brcom.split_broker_submit_id(response.submit_id)
        course = ModelsRegistry.get_course(course_name)

        logger.info(f'Handling result for submit {submit_id} in course {course_name}.')
        broker_submit.update_status(cls.StatusEnum.CHECKED)

        print('unpack results')
        with InCourse(course.short_name):
            Result.objects.unpack_results(submit_id, response)
            submit = Submit.objects.get(pk=submit_id)
            submit.score()
            print(submit)
        print('done')

        broker_submit.update_status(cls.StatusEnum.SAVED)

    @classmethod
    def handle_error(cls, response: brcom.BrokerToBacaError):
        """
        Handles error from broker and sets status of corresponding submit to ERROR.

        :param response: response from broker
        :type response: brcom.BrokerToBacaError
        """
        broker_submit = cls.authenticate(response)
        broker_submit.update_status(cls.StatusEnum.ERROR)
        broker_submit.submit.end_with_error(ResultStatus.INT,
                                            response.error_data['message'] + '\n' +
                                            response.error_data['traceback'])

    @property
    def solution(self):
        """
        Returns source code of this submit.

        :return: source code of this submit
        """  # TODO: specify return type
        with InCourse(self.course.short_name):
            return Submit.objects.get(id=self.submit_id).source_code

    @transaction.atomic
    def update_status(self, new_status: StatusEnum):
        """
        Updates status of this submit.

        :param new_status: new status of this submit
        :type new_status: StatusEnum
        """
        self.status = new_status
        self.update_date = timezone.now()
        self.save()
