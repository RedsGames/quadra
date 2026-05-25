"""Persistent JSON-backed email send queue."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import EmailMessage, EmailStatus, QueueItem

logger = logging.getLogger("email_sender.queue")


class QueueManager:
    """Manages a file-backed FIFO queue of :class:`~src.models.QueueItem` objects.

    The queue is stored as a JSON array on disk so it survives process
    restarts.  All mutating operations read → modify → write atomically
    (within a single process; no cross-process locking is implemented).

    Args:
        queue_file: Path to the JSON queue file.  Created automatically.
        max_retries: Number of allowed delivery attempts before an item is
            marked :attr:`~EmailStatus.FAILED` permanently.
    """

    def __init__(self, queue_file: Path, max_retries: int = 3) -> None:
        self._queue_file = queue_file
        self._max_retries = max_retries
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def _load(self) -> List[dict]:
        if not self._queue_file.exists():
            return []
        with self._queue_file.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self, items: List[dict]) -> None:
        with self._queue_file.open("w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=2)

    @staticmethod
    def _item_to_dict(item: QueueItem) -> dict:
        return {
            "item_id": item.item_id,
            "created_at": item.created_at,
            "status": item.status.value,
            "retries": item.retries,
            "last_error": item.last_error,
            "sent_at": item.sent_at,
            "message": {
                "to": item.message.to,
                "subject": item.message.subject,
                "body_html": item.message.body_html,
                "body_text": item.message.body_text,
                "cc": item.message.cc,
                "bcc": item.message.bcc,
            },
        }

    @staticmethod
    def _dict_to_item(data: dict) -> QueueItem:
        msg_data = data["message"]
        message = EmailMessage(
            to=msg_data["to"],
            subject=msg_data["subject"],
            body_html=msg_data["body_html"],
            body_text=msg_data.get("body_text"),
            cc=msg_data.get("cc", []),
            bcc=msg_data.get("bcc", []),
        )
        return QueueItem(
            message=message,
            item_id=data["item_id"],
            created_at=data["created_at"],
            status=EmailStatus(data["status"]),
            retries=data["retries"],
            last_error=data.get("last_error"),
            sent_at=data.get("sent_at"),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, message: EmailMessage) -> str:
        """Enqueue *message* and return the new item's UUID string."""
        item = QueueItem(message=message, item_id=str(uuid.uuid4()))
        items = self._load()
        items.append(self._item_to_dict(item))
        self._save(items)
        logger.info("Enqueued id=%s subject='%s'", item.item_id, message.subject)
        return item.item_id

    def get_pending(self) -> List[QueueItem]:
        """Return items whose status is PENDING or RETRYING."""
        actionable = {EmailStatus.PENDING.value, EmailStatus.RETRYING.value}
        return [self._dict_to_item(d) for d in self._load() if d["status"] in actionable]

    def get_all(self) -> List[QueueItem]:
        """Return every item in the queue regardless of status."""
        return [self._dict_to_item(d) for d in self._load()]

    def mark_sent(self, item_id: str) -> None:
        """Record a successful delivery for *item_id*."""
        items = self._load()
        for item in items:
            if item["item_id"] == item_id:
                item["status"] = EmailStatus.SENT.value
                item["sent_at"] = datetime.now().isoformat()
                break
        self._save(items)
        logger.info("Marked sent: %s", item_id)

    def mark_failed(self, item_id: str, error: str) -> None:
        """Increment the retry counter for *item_id* or mark it permanently failed.

        The item is set to RETRYING until ``max_retries`` is reached, then FAILED.
        """
        items = self._load()
        for item in items:
            if item["item_id"] == item_id:
                item["retries"] += 1
                item["last_error"] = error
                if item["retries"] >= self._max_retries:
                    item["status"] = EmailStatus.FAILED.value
                    logger.warning(
                        "Permanently failed id=%s after %d retries: %s",
                        item_id,
                        item["retries"],
                        error,
                    )
                else:
                    item["status"] = EmailStatus.RETRYING.value
                    logger.info(
                        "Will retry id=%s (%d/%d): %s",
                        item_id,
                        item["retries"],
                        self._max_retries,
                        error,
                    )
                break
        self._save(items)

    def stats(self) -> Dict[str, int]:
        """Return a dict of ``{status: count, ..., 'total': n}``."""
        items = self._load()
        counts: Dict[str, int] = {s.value: 0 for s in EmailStatus}
        for item in items:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        counts["total"] = len(items)
        return counts
