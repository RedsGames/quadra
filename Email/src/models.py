"""Data models for the email auto-sender."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class EmailStatus(str, Enum):
    """Possible lifecycle states of a queued email."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class EmailMessage:
    """Represents an email message ready to be sent.

    Args:
        to: One or more recipient addresses.
        subject: Email subject line.
        body_html: HTML body content.
        cc: Carbon-copy recipients.
        bcc: Blind carbon-copy recipients.
        body_text: Optional plain-text fallback body.
    """

    to: List[str]
    subject: str
    body_html: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    body_text: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.to, str):
            self.to = [self.to]
        if isinstance(self.cc, str):
            self.cc = [self.cc]
        if isinstance(self.bcc, str):
            self.bcc = [self.bcc]


@dataclass
class QueueItem:
    """Represents an email message stored in the send queue.

    Args:
        message: The email payload.
        item_id: Unique queue identifier (UUID).
        created_at: ISO-8601 timestamp of enqueue time.
        status: Current lifecycle status.
        retries: Number of failed send attempts so far.
        last_error: Description of the most recent failure, if any.
        sent_at: ISO-8601 timestamp of successful delivery, if any.
    """

    message: EmailMessage
    item_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: EmailStatus = EmailStatus.PENDING
    retries: int = 0
    last_error: Optional[str] = None
    sent_at: Optional[str] = None
