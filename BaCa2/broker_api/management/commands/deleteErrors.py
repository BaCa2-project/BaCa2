from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

import logging

from core.settings import BrokerRetryPolicy
from broker_api.models import BrokerSubmit


class Command(BaseCommand):
    help = 'Deletes old error submits'

    deletion_timeout: float = BrokerRetryPolicy.deletion_timeout

    def handle(self, *args, **options):
        print(f"Command {__file__} called.")
        BrokerSubmit.objects.filter(
            status=BrokerSubmit.StatusEnum.ERROR,
            update_date__lte=timezone.now() - timedelta(seconds=self.deletion_timeout)
        ).delete()
