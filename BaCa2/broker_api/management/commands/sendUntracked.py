import logging

from django.core.management.base import BaseCommand

from course.manager import resend_pending_submits

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Searches for "PND" submits, and adds them to tracking system'  # noqa: A003

    def handle(self, *args, **options):
        resent_submits = resend_pending_submits()

        if resent_submits:
            logger.info(f'Resent {resent_submits} submits.')
        else:
            logger.debug('No submits to resend.')
