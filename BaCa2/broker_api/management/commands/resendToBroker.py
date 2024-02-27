import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from broker_api.models import BrokerSubmit
from core.choices import ResultStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Resends expired submits'  # noqa: A003

    # maximum number of retries
    retry_limit: int = settings.BROKER_RETRY_POLICY.resend_max_retries

    def handle(self, *args, **options):
        data = BrokerSubmit.objects.filter(status=BrokerSubmit.StatusEnum.EXPIRED)
        submits_resent = 0
        submits_exceeded = 0
        for submit in data:
            if submit.retry_amount < self.retry_limit:
                if submit.status == BrokerSubmit.StatusEnum.EXPIRED:
                    submit.resend()
                    submits_resent += 1
            else:
                submit.submit.end_with_error(ResultStatus.INT, 'Retry limit exceeded')
                submit.update_status(BrokerSubmit.StatusEnum.ERROR)
                submits_exceeded += 1

        logger.info(f'Command {Path(__file__).name} called - resent {submits_resent} submits, '
                    f'{submits_exceeded} submits exceeded retry limit.')
