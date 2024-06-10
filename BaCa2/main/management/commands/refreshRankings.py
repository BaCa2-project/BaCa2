import logging

from django.core.management.base import BaseCommand

from main.models import Course

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refresh rankings in all courses'  # noqa: A003

    def handle(self, *args, **options):
        Course.objects.update_rankings()
        logger.debug('Rankings refreshed.')
