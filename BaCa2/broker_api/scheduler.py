"""Contains the scheduler for the broker_api app."""

from django.conf import settings
from django.core.management import call_command

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval',
                         minutes=settings.BROKER_RETRY_POLICY.retry_check_interval)
def check_model_updates():
    """Looks for submits that need to be resent to broker, marks them expired and resends them."""
    call_command('markExpired')
    call_command('resendToBroker')


@scheduler.scheduled_job('interval',
                         minutes=settings.BROKER_RETRY_POLICY.deletion_check_interval)
def delete_old_errors():
    """Deletes errors that are older than BrokerRetryPolicy.error_deletion_time."""
    call_command('deleteErrors')


@scheduler.scheduled_job('interval',
                         minutes=settings.BROKER_RETRY_POLICY.untracked_check_interval)
def send_untracked():
    """Checks for submits that were not tracked by the broker api app and sends them."""
    call_command('sendUntracked')
