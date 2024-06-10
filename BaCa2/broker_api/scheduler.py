"""Contains the scheduler for the broker_api app."""

from django.conf import settings
from django.core.management import call_command


def check_model_updates():
    """Looks for submits that need to be resent to broker, marks them expired and resends them."""
    call_command('markExpired')
    call_command('resendToBroker')


def delete_old_errors():
    """Deletes errors that are older than BrokerRetryPolicy.error_deletion_time."""
    call_command('deleteErrors')


def send_untracked():
    """Checks for submits that were not tracked by the broker api app and sends them."""
    call_command('sendUntracked')


JOBS = [
    {
        'func': check_model_updates,
        'trigger': 'interval',
        'minutes': settings.BROKER_RETRY_POLICY.retry_check_interval
    },
    {
        'func': delete_old_errors,
        'trigger': 'interval',
        'minutes': settings.BROKER_RETRY_POLICY.deletion_check_interval
    },
    {
        'func': send_untracked,
        'trigger': 'interval',
        'minutes': settings.BROKER_RETRY_POLICY.untracked_check_interval
    }
]
