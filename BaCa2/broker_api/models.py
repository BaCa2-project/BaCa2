
from django.db import models
from django.utils import timezone

from main.models import Course
from package.models import PackageInstance
from course.routing import InCourse
from course.models import Submit

class BrokerSubmit(models.Model):

    class StatusEnum(models.IntegerChoices):
        EXPIRED = -1
        NEW = 0
        AWAITING_RESPONSE = 1
        CHECKED = 2

    # `course` and `submit_id` make up the primary key
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    submit_id = models.BigIntegerField()

    package_instance = models.ForeignKey(PackageInstance, on_delete=models.CASCADE)
    status = models.IntegerField(StatusEnum, default=StatusEnum.NEW)

    update_date = models.DateTimeField(default=timezone.now)

    @property
    def solution(self):
        with InCourse(str(self.course)):
            return Submit.objects.get(id=self.submit_id).first().source_code
        # TODO: Check if it works

    def update_status(self, new_status: StatusEnum):
        # new_status is purely for safety reasons
        if new_status - 1 != self.status:
            raise ValueError(f"Attempted to change status from {self.status} to {new_status}.")
        self.status = new_status
        self.update_date = timezone.now()
        self.save()
