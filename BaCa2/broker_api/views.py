from django.shortcuts import render
from django.http import HttpResponse

from .communicate import BrokerSubmitManager


def handle_broker(request, course: str, submit_id: int):
    instance = BrokerSubmitManager.instance
    success = instance.handle(course, submit_id)
    if success:
        return HttpResponse("failure")
    else:
        return HttpResponse("success")
