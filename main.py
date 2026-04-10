import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler.signal_runner import run_signal_scan
from notifications.telegram import send_eod_close_reminder
from monitoring.logger import log

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scan_times = [
        (12, 20),
    ]
    for hour, minute in scan_times:
        scheduler.add_job(
            run_signal_scan,
            CronTrigger(hour=hour, minute=minute, timezone="America/New_York"),
        )
    scheduler.add_job(
        send_eod_close_reminder,
        CronTrigger(hour=15, minute=50, timezone="America/New_York"),
    )
    scheduler.start()
    log.info("Freki scheduled — daily scan at 12:20 ET + EOD alert at 15:50 ET. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)
        log.info("Scheduler stopped.")
