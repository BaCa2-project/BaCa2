from broker_api.scheduler import scheduler
from BaCa2.settings import BrokerRetryPolicy

# Start the scheduler
if BrokerRetryPolicy.auto_start:
    scheduler.start()
