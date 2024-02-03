from typing import Any, Dict, Iterable

import usosapi

from . import *


class RegisterUSOS:
    def __init__(self):
        self.connection = usosapi.USOSAPIConnection(
            api_base_address=USOS_GATEWAY,
            consumer_key=USOS_CONSUMER_KEY,
            consumer_secret=USOS_CONSUMER_SECRET
        )
        self.token_key = None
        self.token_secret = None
        self.scopes = '|'.join([str(scope) for scope in USOS_SCOPES])

    @property
    def authorization_url(self):
        return self.connection.get_authorization_url()

    def authorize_with_pin(self, pin):
        self.connection.authorize_with_pin(pin)
        self.token_key, self.token_secret = self.connection.get_access_data()

    @property
    def token(self):
        return self.token_key, self.token_secret


class USOS:
    def __init__(self, token_key, token_secret):
        self.connection = usosapi.USOSAPIConnection(
            api_base_address=USOS_GATEWAY,
            consumer_key=USOS_CONSUMER_KEY,
            consumer_secret=USOS_CONSUMER_SECRET
        )
        self.connection.set_access_data(token_key, token_secret)

    def get_user_data(self,
                      user_id=None,
                      fields: Iterable[str] = ('id',
                                               'first_name',
                                               'last_name',
                                               'email',
                                               'sex',
                                               'titles',
                                               'student_number')) -> Dict[str, Any]:
        """
        It gets user data from USOS API. If user_id is None, it gets data of the user who is
        logged in. Fields are specified in the fields parameter. If fields is None, it gets only
        ``id``, ``first_name`` and ``last_name``.

        Possible fields are described in the `USOS API documentation
        <https://apps.usos.uj.edu.pl/developers/api/services/users/#user>`_.

        :param user_id: USOS user id (if None, it gets data of the user who is logged in)
        :param fields: fields to get
        :type fields: Iterable[str]

        :return: user data
        :rtype: Dict[str, Any]
        """
        fields_str = '|'.join(fields)
        if user_id:
            return self.connection.get('services/users/user',
                                       user_id=user_id,
                                       fields=fields_str)
        else:
            return self.connection.get('services/users/user',
                                       fields=fields_str)

    def get_user_courses(self):
        """
        It gets courses of the user. If user_id is None, it gets courses of the user who is
        logged in. It gets only active courses by default, but you can change it by setting
        active_terms_only to False.

        :param user_id: USOS user id (if None, it gets courses of the user who is logged in)
        :param active_terms_only: if True, it gets only active courses
        :type active_terms_only: bool

        :return: courses of the user
        """
        courses = self.connection.get('services/courses/user')

        return courses
