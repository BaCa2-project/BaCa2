from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from BaCa2.settings import BROKER_RETRY
from broker_api.models import BrokerSubmit


class Command(BaseCommand):
    help = 'Marks expired submits as such'

    retry_timeout: float = BROKER_RETRY['expiration timeout']

    def handle(self, *args, **options):
        data = BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
            update_date__lte=timezone.now() - timedelta(seconds=self.retry_timeout)
        )
        for submit in data:
            submit.update_date = timezone.now()
            submit.update_status(BrokerSubmit.StatusEnum.EXPIRED)
