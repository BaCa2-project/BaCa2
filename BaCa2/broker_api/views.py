import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import BrokerSubmit
from baca2PackageManager.broker_communication import *


@csrf_exempt
def handle_broker_result(request):
    if request.method != 'POST':
        return HttpResponse("Not found", 404)

    if request.headers.get('content-type') != 'application/json':
        return HttpResponse("Wrong argument", 400)

    try:
        data = BrokerToBaca.parse(json.loads(request.body))
        BrokerSubmit.handle_result(data)
    except Exception as e:
        return HttpResponse(str(e), 401)
    else:
        return HttpResponse("Good", 200)


@csrf_exempt
def handle_broker_error(request):
    if request.method != 'POST':
        return HttpResponse("Not found", 404)

    if request.headers.get('content-type') != 'application/json':
        return HttpResponse("Wrong argument", 400)

    try:
        data = BrokerToBacaError.parse(json.loads(request.body))
        BrokerSubmit.handle_error(data)
    except Exception as e:
        return HttpResponse(str(e), 401)
    else:
        return HttpResponse("Good", 200)
