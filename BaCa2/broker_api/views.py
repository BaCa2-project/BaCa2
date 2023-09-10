import json

from django.shortcuts import render
from django.http import HttpResponse

from .communicate import BrokerSubmitManager
from .message import BrokerToBaca, Test


def handle_broker_result(request, course: str, submit_id: int):
    if request.method != 'POST':
        return HttpResponse("Not found", 404)

    if request.headers.get('content-type') != 'application/json':
        return HttpResponse("Wrong argument", 400)

    instance = BrokerSubmitManager.instance

    data = json.loads(request.body)
    data['tests'] = list(map(lambda x: Test(**x), data['tests']))
    btb_data = BrokerToBaca(**data)
    instance.handle_result(course, submit_id, btb_data)
    return HttpResponse("Good", 200)


def handle_broker_status(request, course: str, submit_id: int):
    ...
