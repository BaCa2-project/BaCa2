import os

USOS_CONSUMER_KEY = os.getenv('USOS_CONSUMER_KEY')
USOS_CONSUMER_SECRET = os.getenv('USOS_CONSUMER_SECRET')
USOS_GATEWAY = os.getenv('USOS_GATEWAY')
USOS_SCOPES = [
    'offline_access',
    'crstests',
    'email',
    'grades',
    'grades_write',
    'mailclient',
    'other_emails',
    'staff_perspective',
]