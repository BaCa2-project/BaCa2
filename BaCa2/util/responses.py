from __future__ import annotations

from enum import Enum

from django.http import JsonResponse

from core.choices import ModelAction
from util.models import model_cls


class BaCa2JsonResponse(JsonResponse):
    """
    Base class for all JSON responses returned as a result of an AJAX POST or GET request sent in
    the BaCa2 web app. Contains basic  fields required by views to handle the response along with
    predefined values for the status field.

    See Also:
        :class:`util.views.BaCa2ModelView`
        :class:`BaCa2Form`
        :class:`FormWidget`
    """

    class Status(Enum):
        """
        Enum used to indicate the possible outcomes of an AJAX POST or GET request sent in
        the BaCa2 web app.
        """
        #: Indicates that the request was successful.
        SUCCESS = 'success'
        #: Indicates that the request was unsuccessful due to invalid data.
        INVALID = 'invalid'
        #: Indicates that the request was unsuccessful due to the sender's lack of necessary
        #: permissions.
        IMPERMISSIBLE = 'impermissible'
        #: Indicates that the request was unsuccessful due to an internal error.
        ERROR = 'error'

    def __init__(self, status: Status, message: str = '', **kwargs: dict) -> None:
        """
        :param status: Status of the response.
        :type status: :class:`BaCa2JsonResponse.Status`
        :param message: Message accompanying the response.
        :type message: str
        :param kwargs: Additional fields to be included in the response.
        :type kwargs: dict
        """
        super().__init__({'status': status.value, 'message': message} | kwargs)


class BaCa2ModelResponse(BaCa2JsonResponse):
    """
    Base class for all JSON responses returned as a result of an AJAX POST request sent by a model
    form or GET request sent to a model view in the BaCa2 web app.

    See Also:
        :class:`util.views.BaCa2ModelView`
        :class:`BaCa2ModelForm`
        :class:`BaCa2JsonResponse`
    """

    def __init__(self,
                 model: model_cls,
                 action: ModelAction,
                 status: BaCa2JsonResponse.Status,
                 message: str = '',
                 **kwargs: dict) -> None:
        """
        :param model: Model class which instances the request pertains to.
        :type model: Type[Model]
        :param action: Action the request pertains to.
        :type action: :class:`ModelAction`
        :param status: Status of the response.
        :type status: :class:`BaCa2JsonResponse.Status`
        :param message: Message accompanying the response. If no message is provided, a default
            message will be generated based on the status of the response, the model and the action
            performed.
        :type message: str
        :param kwargs: Additional fields to be included in the response.
        :type kwargs: dict
        """
        if not message:
            message = self.generate_response_message(status, model, action)
        super().__init__(status, message, **kwargs)

    @staticmethod
    def generate_response_message(status, model, action) -> str:
        """
        Generates a response message based on the status of the response, the model and the action
        performed.

        :param status: Status of the response.
        :type status: :class:`BaCa2JsonResponse.Status`
        :param model: Model class which instances the request pertains to.
        :type model: Type[Model]
        :param action: Action the request pertains to.
        :type action: :class:`ModelAction`
        :return: Response message.
        :rtype: str
        """
        model_name = model._meta.verbose_name

        if status == BaCa2JsonResponse.Status.SUCCESS:
            return f'successfully performed {action.label} on {model_name}'

        message = f'failed to perform {action.label} on {model_name}'

        if status == BaCa2JsonResponse.Status.INVALID:
            message += ' due to invalid form data. Please correct the following errors:'
        elif status == BaCa2JsonResponse.Status.IMPERMISSIBLE:
            message += ' due to insufficient permissions.'
        elif status == BaCa2JsonResponse.Status.ERROR:
            message += ' due an error.'

        return message
