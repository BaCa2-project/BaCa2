from typing import Optional
from pathlib import Path
import json
import http.client as client

from .models import BrokerSubmit
import baca2PackageManager as Bpm

from main.models import Course


class BrokerSubmitManager:

    instance: Optional['BrokerSubmitManager'] = None

    def __new__(cls, *args, **kwargs):
        cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, ip_address: str, port: int, timeout: float = 30):
        self.ip = ip_address
        self.port = port
        self.timeout = timeout

    def _send_submit(self, submit: BrokerSubmit) -> bool:
        connection = client.HTTPConnection(host=self.ip, port=self.port, timeout=self.timeout)
        content = {
            "course": submit.course.name,
            "submit_id": submit.submit_id,
            "package_path": submit.package_path,
            "solution_path": submit.solution_path,
            "output_path": submit.output_path
        }
        bin_content = bin(json.dumps(content))
        connection.putheader('Accept', 'application/json')
        connection.putheader("Content-Length", str(len(bin_content)))
        connection.endheaders()
        connection.send(bin_content)
        out = connection.getresponse() == 200
        connection.close()
        return out

    def add_and_send(self,
                     course: Course,
                     submit_id: int,
                     package: Bpm.Package,
                     solution: Path,
                     output_path: Path) -> BrokerSubmit:
        if BrokerSubmit.objects.filter(course=course, submit_id=submit_id).exists():
            raise Exception
        new_submit = BrokerSubmit.objects.create(
            course=course,
            submit_id=submit_id,
            package_path=package.commit_path,
            solution_path=solution,
            output_path=output_path,
            status=BrokerSubmit.StatusEnum.NEW
        )
        success = self._send_submit(new_submit)
        if not success:
            raise Exception  # TODO
        new_submit.update_status(BrokerSubmit.StatusEnum.AWAITING_RESPONSE)
        return new_submit

    @staticmethod
    def handle(course: str, submit_id: int) -> bool:
        submit = BrokerSubmit.objects.get(course__name=course, submit_id=submit_id)
        if submit is None:
            return False
        submit.update_status(BrokerSubmit.StatusEnum.CHECKED)
        ...  # TODO
