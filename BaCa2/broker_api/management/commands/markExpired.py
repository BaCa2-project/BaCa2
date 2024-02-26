from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.utils import timezone

from broker_api.models import BrokerSubmit
from core.choices import ResultStatus


class Command(BaseCommand):
    help = 'Marks expired submits, and resends them as new'  # noqa: A003

    retry_timeout: float = settings.BROKER_RETRY_POLICY.expiration_timeout

    def handle(self, *args, **options):
        print(f'Command {__file__} called.')
        data = BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
            update_date__lte=timezone.now() - timedelta(seconds=self.retry_timeout)
        )
        for submit in data:
            submit.update_status(BrokerSubmit.StatusEnum.ERROR)
            submit.submit.end_with_error(ResultStatus.ITL)
            try:
                submit.submit.resend(settings.BROKER_RETRY_POLICY.resend_max_retries)
            except ValidationError:
                pass
