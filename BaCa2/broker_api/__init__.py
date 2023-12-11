from broker_api.scheduler import scheduler
from BaCa2.settings import BROKER_RETRY

if BROKER_RETRY['auto start']:
    scheduler.start()
