from pathlib import Path
import http.client as client

from .models import BrokerSubmit
import baca2PackageManager as Bpm

from ..main.models import Course


class BrokerSender:

    def __init__(self, ip_address: str, port: int):
        self.ip_address = ip_address
        self.port = port

    def send(self, submit: BrokerSubmit):
        if submit.status not in [BrokerSubmit.StatusEnum.NEW, BrokerSubmit.StatusEnum.EXPIRED]:
            raise Exception  # TODO
        ...


class BrokerSubmitManager:

    @staticmethod
    def add_and_send(course: Course, submit_id: int, package: Bpm.Package, solution: Path) -> BrokerSubmit:
        if BrokerSubmit.objects.filter(course=course, submit_id=submit_id).exists():
            raise Exception
        new_submit = BrokerSubmit.objects.create(
            course=course,
            submit_id=submit_id,
            package_path=package.commit_path,
            solution_path=solution,
            solution=BrokerSubmit.StatusEnum.NEW
        )
        ...
