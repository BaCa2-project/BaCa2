from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from broker_api.models import BrokerSubmit
from django.conf import settings


class Command(BaseCommand):
    help = 'Deletes old error submits'

    deletion_timeout: float = settings.BROKER_RETRY_POLICY.deletion_timeout

    def handle(self, *args, **options):
        print(f"Command {__file__} called.")
        BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.ERROR,
            update_date__lte=timezone.now() - timedelta(seconds=self.deletion_timeout)
        ).delete()
