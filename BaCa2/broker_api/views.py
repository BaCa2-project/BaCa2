import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import BrokerSubmit
from baca2PackageManager.broker_communication import *


@csrf_exempt
def handle_broker_result(request):
    """
    Handles the result sent by the broker.

    This function is exempt from CSRF verification. It expects a POST request with a JSON body.
    The JSON body is parsed and handled by the BrokerSubmit.handle_result method.

    Possible status codes:

    * If the request method is not POST, it returns 404.
    * If the content type of the request is not 'application/json', it returns 400.
    * If there is a PermissionError during the processing of the request, it returns 401.
    * If there is any other exception during the processing of the request, it returns 403.
    * If the request is processed successfully, it returns 200.

    :param request: The HTTP request received from the broker.
    :type request: django.http.HttpRequest
    :return: An HTTP response. The status code of the response depends on the processing of the request.
    :rtype: django.http.HttpResponse
    """
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
    """
    Handles the error sent by the broker.

    This function is exempt from CSRF verification. It expects a POST request with a JSON body.
    The JSON body is parsed and handled by the BrokerSubmit.handle_error method.

    Possible status codes:

    * If the request method is not POST, it returns 404.
    * If the content type of the request is not 'application/json', it returns 400.
    * If there is a PermissionError during the processing of the request, it returns 401.
    * If there is any other exception during the processing of the request, it returns 403.
    * If the request is processed successfully, it returns 200.

    :param request: The HTTP request received from the broker.
    :type request: django.http.HttpRequest
    :return: An HTTP response. The status code of the response depends on the processing of the request.

    :rtype: django.http.HttpResponse
    """
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
