from django.core.management.base import BaseCommand
from django.utils import timezone

from datetime import timedelta

from BaCa2.settings import BROKER_RETRY
from broker_api.models import BrokerSubmit


class RetryCommand(BaseCommand):
    help = 'Handles retries for failed submits'

    # retry time in seconds
    retry_timeout: float = BROKER_RETRY['retry timeout']
    # maximum number of retries
    retry_limit: int = BROKER_RETRY['max retries']

    def handle(self, *args, **options):
        to_be_resent = BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
            update_date__lte=timezone.now() - timedelta(seconds=self.retry_timeout)
        )
        for submit in to_be_resent:
            if submit.retries >= self.retry_limit:
                submit.update_status(BrokerSubmit.StatusEnum.EXPIRED)
            else:
                submit.retries += 1
                submit.save()
                submit.send_submit()
