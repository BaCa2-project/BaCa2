from django.core.management.base import BaseCommand
from django.utils import timezone

import logging

from BaCa2.settings import BROKER_RETRY
from broker_api.models import BrokerSubmit


class Command(BaseCommand):
    help = 'Resends expired submits'

    # maximum number of retries
    retry_limit: int = BROKER_RETRY['resend max retries']

    def handle(self, *args, **options):
        print(f"Command {__file__} called.")
        data = BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.EXPIRED)
        for submit in data:
            if submit.retries >= self.retry_limit:
                submit.update_date = timezone.now()
                submit.update_status(BrokerSubmit.StatusEnum.ERROR)
                submit.save()
            else:
                submit.retries += 1
                submit.update_date = timezone.now()
                submit.update_status(BrokerSubmit.StatusEnum.AWAITING_RESPONSE)
                submit.save()
                submit.send_submit()
