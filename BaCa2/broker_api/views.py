import json

from django.http import HttpResponse

from .models import BrokerSubmit
from baca2PackageManager.broker_communication import *


def handle_broker_result(request, broker_submit_id: str):
    if request.method != 'POST':
        return HttpResponse("Not found", 404)

    if request.headers.get('content-type') != 'application/json':
        return HttpResponse("Wrong argument", 400)

    try:
        data = BrokerToBaca.parse(json.loads(request.body))
        BrokerSubmit.handle_result(broker_submit_id, data)
    except Exception as e:
        return HttpResponse(str(e), 401)
    else:
        return HttpResponse("Good", 200)


def handle_broker_status(request, course: str, submit_id: int):
    ...
