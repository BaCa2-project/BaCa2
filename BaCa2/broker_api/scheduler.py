from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from BaCa2.settings import BROKER_RETRY


scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval', minutes=BROKER_RETRY['retry check interval'])
def check_model_updates():
    call_command('resend_to_broker')


@receiver(post_migrate)
def start_scheduler(sender, **kwargs):
    scheduler.start()
