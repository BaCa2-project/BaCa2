from django.core.management.base import BaseCommand

from broker_api.models import BrokerSubmit
from core.settings import BrokerRetryPolicy


class Command(BaseCommand):
    help = 'Resends expired submits'  # noqa: A003

    # maximum number of retries
    retry_limit: int = BrokerRetryPolicy.resend_max_retries

    def handle(self, *args, **options):
        print(f'Command {__file__} called.')
        data = BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.EXPIRED)
        for submit in data:
            if submit.retry_amount < self.retry_limit:
                submit.resend()
            else:
                submit.update_status(BrokerSubmit.StatusEnum.ERROR)
