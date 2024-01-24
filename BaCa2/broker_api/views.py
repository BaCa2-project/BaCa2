import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import BrokerSubmit
from baca2PackageManager.broker_communication import *


@csrf_exempt
def handle_broker_result(request):
    """Handles result sent by broker."""
    if request.method != 'POST':
        return HttpResponse("Not found", status=404)

    if request.headers.get('content-type') != 'application/json':
        return HttpResponse("Wrong argument", status=400)

    try:
        data = BrokerToBaca.parse(json.loads(request.body))
        BrokerSubmit.handle_result(data)
    except PermissionError as e:
        return HttpResponse(str(e), status=401)
    except Exception as e:
        return HttpResponse(str(e), status=403)
    else:
        return HttpResponse("Good", status=200)


@csrf_exempt
def handle_broker_error(request):
    """Handles error sent by broker."""
    if request.method != 'POST':
        return HttpResponse("Not found", status=404)

    if request.headers.get('content-type') != 'application/json':
        return HttpResponse("Wrong argument", status=400)

    try:
        data = BrokerToBacaError.parse(json.loads(request.body))
        BrokerSubmit.handle_error(data)
    except PermissionError as e:
        return HttpResponse(str(e), status=401)
    except Exception as e:
        return HttpResponse(str(e), status=403)
    else:
        return HttpResponse("Good", status=200)
