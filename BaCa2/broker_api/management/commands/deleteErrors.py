import logging
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from broker_api.models import BrokerSubmit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Deletes old error submits'  # noqa: A003

    deletion_timeout: float = settings.BROKER_RETRY_POLICY.deletion_timeout

    def handle(self, *args, **options):
        submits_to_delete = BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.ERROR,
            update_date__lte=timezone.now() - timedelta(seconds=self.deletion_timeout)
        )
        delete_amount = len(submits_to_delete)
        submits_to_delete.delete()

        if delete_amount:
            logger.info(f'Deleted {delete_amount} submits.')
        else:
            logger.debug('No submits to delete.')
