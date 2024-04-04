from django.conf import settings

from broker_api.scheduler import scheduler

# Start the scheduler
if settings.BROKER_RETRY_POLICY.auto_start:
    scheduler.start()
