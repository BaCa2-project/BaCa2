from django.conf import settings
from django.core.management import call_command


def refresh_rankings() -> None:
    """
    Refresh rankings in all courses - job to be scheduled
    """
    call_command('refreshRankings')


REFRESH_RANKINGS_JOB = {
    'func': refresh_rankings,
    'trigger': 'interval',
    'seconds': settings.RANKING_REFRESH_RATE
}
