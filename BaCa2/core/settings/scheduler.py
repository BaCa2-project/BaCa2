from apscheduler.schedulers.background import BackgroundScheduler

SCHEDULER = BackgroundScheduler()

SCHEDULER.start()

# ---------------------

RANKING_REFRESH_RATE = 60 * 5  # 5 minutes
AUTO_REFRESH_RANKINGS = True
