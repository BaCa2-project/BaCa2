from broker_api.scheduler import scheduler
from BaCa2.settings import BrokerRetryPolicy

if BrokerRetryPolicy.auto_start:
    scheduler.start()
