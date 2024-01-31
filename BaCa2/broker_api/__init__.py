from broker_api.scheduler import scheduler
from core.settings import BrokerRetryPolicy

# Start the scheduler
if BrokerRetryPolicy.auto_start:
    scheduler.start()
