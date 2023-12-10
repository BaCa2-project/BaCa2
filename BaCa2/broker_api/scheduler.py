from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

from BaCa2.settings import BROKER_RETRY


scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval', minutes=BROKER_RETRY['retry check interval'])
def check_model_updates():
    call_command('markExpired')
    call_command('resendToBroker')


@scheduler.scheduled_job('interval', minutes=BROKER_RETRY['delete check interval'])
def delete_old_errors():
    call_command('deleteErrors')


scheduler.start()
