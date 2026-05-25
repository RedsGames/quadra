"""Менеджер очереди email с APScheduler."""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


class EmailQueueManager:
    def __init__(self, mailer):
        self.mailer = mailer
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs: list[dict] = []

    def send_now(self, to: str, subject: str, body: str) -> dict:
        try:
            self.mailer.send(to, subject, body)
            entry = {"to": to, "subject": subject, "status": "sent", "sent_at": datetime.now().isoformat()}
        except Exception as e:
            entry = {"to": to, "subject": subject, "status": "error", "error": str(e), "sent_at": datetime.now().isoformat()}
            logger.error("Email send failed: %s", e)
        self.jobs.append(entry)
        return entry

    def schedule(self, to: str, subject: str, body: str, run_date: datetime) -> dict:
        job_id = f"email_{len(self.jobs)}"
        entry = {"id": job_id, "to": to, "subject": subject, "status": "scheduled", "run_at": run_date.isoformat()}
        self.jobs.append(entry)

        def _send():
            try:
                self.mailer.send(to, subject, body)
                entry["status"] = "sent"
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)

        self.scheduler.add_job(_send, "date", run_date=run_date, id=job_id)
        return entry

    def get_status(self) -> list[dict]:
        return self.jobs
