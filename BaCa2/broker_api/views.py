import json
import logging
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from baca2PackageManager.broker_communication import *
from main.models import Course

from .models import BrokerSubmit

# Initialize logger
logger = logging.getLogger(__name__)


def initial_request_check(request) -> HttpResponse | None:
    """
    Performs an initial check on the HTTP request.

    This function checks if the request method is POST and if the content type of the request
    is 'application/json'. If any of these checks fail, it returns an HTTP response with
    an appropriate status code and message. If all checks pass, it returns None.

    Possible status codes:

    * If the request method is not POST, it returns `405` (Method Not Allowed).
    * If the content type of the request is not 'application/json',
        it returns `415` (Unsupported Media Type).

    :param request: The HTTP request to check.
    :type request: django.http.HttpRequest
    :return: An HTTP response if any of the checks fail, None otherwise.
    :rtype: django.http.HttpResponse | None
    """
    # Check if the request method is POST
    if request.method != 'POST':
        return HttpResponse('Method other then POST is not allowed.', status=405)

    # Check if the content type of the request is 'application/json'
    if request.headers.get('content-type') != 'application/json':
        return HttpResponse('Wrong argument', status=415)

    return None


def check_submit_id(broker_submit_id: str) -> HttpResponse | None:
    """
    Checks the validity of the submit ID.

    This function splits the broker_submit_id into course_short_name and submit_id.
    It then retrieves the course with the short_name and checks if it exists.
    If the course does not exist, it returns an HTTP response with status code `470` and
    an appropriate message.
    If the course exists, it retrieves the submit with the submit_id and checks if it exists.
    If the submit does not exist, it returns an HTTP response with status code `471` and
    an appropriate message.
    If both the course and the submit exist, it returns None.

    If unknown error occurs, it returns an HTTP response with status code `400`.

    Possible status codes:

    * If the course does not exist, it returns `470` ([internal code]: bad course name).
    * If the submit does not exist, it returns `471` ([internal code]: bad submit id).

    :param broker_submit_id: The submit ID to check.
    :type broker_submit_id: str
    :return: An HTTP response if the course or the submit do not exist, None otherwise.
    :rtype: django.http.HttpResponse | None
    """
    try:
        course_short_name, submit_id = split_broker_submit_id(broker_submit_id)
    except Exception as e:
        logger.warning(f'Failed to split submit id {broker_submit_id}: {e}')
        return HttpResponse(f'Wrong submit id: {e}', status=400)

    try:
        course = Course.objects.get(short_name=course_short_name)
    except Exception as e:
        logger.warning(f'Failed to get course with short name {course_short_name}: {e}')
        return HttpResponse(f'Wrong course name: {course_short_name}', status=470)
    try:
        course.get_submit(submit_id)
    except Exception as e:
        logger.warning(f'Failed to get submit with id {submit_id}: {e}')
        return HttpResponse(f'Wrong submit id: {submit_id}', status=471)
    return None


@csrf_exempt
def handle_broker_result(request):
    """
    Handles the result sent by the broker.

    This function is exempt from CSRF verification. It expects a POST request with a JSON body.
    The JSON body is parsed and handled by the BrokerSubmit.handle_result method.

    Possible status codes:

    * If the request method is not POST, it returns `405` (Method Not Allowed).
    * If the content type of the request is not 'application/json',
        it returns `415` (Unsupported Media Type).
    * If there is a PermissionError during the processing of the request,
        it returns `403` (Forbidden).
    * If there is any other exception during the processing of the request, it returns

        - `550` [internal code]: Parsing error
        - `551` [internal code]: Error, while handling error
        - `552` [internal code]: Error, while handling result

    * If the request is processed successfully, it returns `200` (OK).

    :param request: The HTTP request received from the broker.
    :type request: django.http.HttpRequest
    :return: An HTTP response. The status code of the response depends on the processing of
        the request.
    :rtype: django.http.HttpResponse
    """
    initial_check = initial_request_check(request)
    if initial_check:
        return initial_check

    # Try to parse the JSON body of the request
    try:
        data = BrokerToBaca.parse(json.loads(request.body))

        submit_check = check_submit_id(data.submit_id)
        if submit_check:
            return submit_check
    except Exception as e:
        return HttpResponse(f'Failed to parse data: {e}', status=550)

    # Try to handle the parsed data
    try:
        BrokerSubmit.handle_result(data)
    except PermissionError as e:
        return HttpResponse(f'Authentication failed: {e}', status=403)
    except Exception as e:
        # Log the exception
        logger.error(traceback.format_exc())
        # Create an error object
        error = BrokerToBacaError(
            pass_hash=data.pass_hash,
            submit_id=data.submit_id,
            error=f'Failed to handle result: {e}'
        )
        # Try to handle the error
        try:
            BrokerSubmit.handle_error(error)
        except Exception as e:
            # Log the critical error
            logger.critical(f'Failed to handle error: {e}')
            return HttpResponse(f'Failed to handle error {e}', status=551)
        return HttpResponse(f'Failed to handle result: {e}', status=552)
    else:
        return HttpResponse('Success', status=200)


@csrf_exempt
def handle_broker_error(request):
    """
    Handles the error sent by the broker.

    This function is exempt from CSRF verification. It expects a POST request with a JSON body.
    The JSON body is parsed and handled by the BrokerSubmit.handle_error method.

    Possible status codes:

    * If the request method is not POST, it returns `405` (Method Not Allowed).
    * If the content type of the request is not 'application/json',
        it returns `415` (Unsupported Media Type).
    * If there is a PermissionError during the processing of the request,
        it returns `403` (Forbidden).
    * If there is any other exception during the processing of the request, it returns

        - `550` [internal code]: Parsing error
        - `551` [internal code]: Error, while handling error

    * If the request is processed successfully, it returns `200` (OK).

    :param request: The HTTP request received from the broker.
    :type request: django.http.HttpRequest
    :return: An HTTP response. The status code of the response depends on the processing of
        the request.
    :rtype: django.http.HttpResponse
    """
    initial_check = initial_request_check(request)
    if initial_check:
        return initial_check

    # Try to parse the JSON body of the request
    try:
        data = BrokerToBacaError.parse_obj(json.loads(request.body))

        submit_check = check_submit_id(data.submit_id)
        if submit_check:
            return submit_check
    except Exception as e:
        return HttpResponse(f'Failed to parse data: {e}', status=550)

    # Try to handle the parsed data
    try:
        BrokerSubmit.handle_error(data)
    except PermissionError as e:
        return HttpResponse(f'Authentication failed: {e}', status=403)
    except Exception as e:
        # Log the critical error
        logger.critical(f'Failed to handle error: {e}')
        return HttpResponse(f'Failed to handle error {e}', status=551)
    else:
        return HttpResponse('Success', status=200)
