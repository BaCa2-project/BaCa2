from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from broker_api.models import BrokerSubmit


class Command(BaseCommand):
    help = 'Marks expired submits as such'

    retry_timeout: float = settings.BROKER_RETRY_POLICY.expiration_timeout

    def handle(self, *args, **options):
        print(f"Command {__file__} called.")
        data = BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
            update_date__lte=timezone.now() - timedelta(seconds=self.retry_timeout)
        )
        for submit in data:
            submit.update_status(BrokerSubmit.StatusEnum.EXPIRED)
