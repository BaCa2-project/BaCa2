"""Contains the scheduler for the broker_api app."""

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

from BaCa2.settings import BrokerRetryPolicy


scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval', minutes=BrokerRetryPolicy.retry_check_interval)
def check_model_updates():
    """Looks for submits that need to be resent to broker, marks them expired and resends them."""
    call_command('markExpired')
    call_command('resendToBroker')


@scheduler.scheduled_job('interval', minutes=BrokerRetryPolicy.deletion_check_interval)
def delete_old_errors():
    """Deletes errors that are older than BrokerRetryPolicy.error_deletion_time."""
    call_command('deleteErrors')
