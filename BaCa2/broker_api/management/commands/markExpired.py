import logging
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from broker_api.models import BrokerSubmit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Marks expired submits, and resends them as new'  # noqa: A003

    retry_timeout: float = settings.BROKER_RETRY_POLICY.expiration_timeout

    def handle(self, *args, **options):
        data = BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.AWAITING_RESPONSE,
            update_date__lte=timezone.now() - timedelta(seconds=self.retry_timeout)
        )
        for submit in data:
            if submit.update_date <= timezone.now() - timedelta(seconds=self.retry_timeout):
                submit.update_status(BrokerSubmit.StatusEnum.EXPIRED)

        logger.info(f'Command {Path(__file__).name} called - marked {len(data)} '
                    'submits as expired.')
