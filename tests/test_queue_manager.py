"""Tests for QueueManager — persistence, state transitions, and statistics."""

from pathlib import Path

import pytest

from src.models import EmailMessage, EmailStatus
from src.queue_manager import QueueManager


@pytest.fixture
def queue(tmp_path: Path) -> QueueManager:
    return QueueManager(tmp_path / "queue.json", max_retries=2)


@pytest.fixture
def msg() -> EmailMessage:
    return EmailMessage(
        to=["recipient@example.com"],
        subject="Test Subject",
        body_html="<p>Hello</p>",
    )


class TestAdd:
    def test_returns_string_id(self, queue, msg):
        item_id = queue.add(msg)
        assert isinstance(item_id, str) and len(item_id) > 0

    def test_unique_ids(self, queue, msg):
        ids = {queue.add(msg) for _ in range(5)}
        assert len(ids) == 5

    def test_item_appears_in_pending(self, queue, msg):
        queue.add(msg)
        assert len(queue.get_pending()) == 1

    def test_persists_across_instances(self, tmp_path, msg):
        q1 = QueueManager(tmp_path / "q.json", max_retries=3)
        q1.add(msg)
        q2 = QueueManager(tmp_path / "q.json", max_retries=3)
        assert len(q2.get_all()) == 1


class TestMarkSent:
    def test_status_changes_to_sent(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_sent(item_id)
        item = queue.get_all()[0]
        assert item.status == EmailStatus.SENT

    def test_sent_at_is_populated(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_sent(item_id)
        item = queue.get_all()[0]
        assert item.sent_at is not None

    def test_sent_item_not_in_pending(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_sent(item_id)
        assert queue.get_pending() == []


class TestMarkFailed:
    def test_first_failure_sets_retrying(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_failed(item_id, "Timeout")
        item = queue.get_all()[0]
        assert item.status == EmailStatus.RETRYING
        assert item.retries == 1

    def test_last_error_recorded(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_failed(item_id, "Connection refused")
        item = queue.get_all()[0]
        assert item.last_error == "Connection refused"

    def test_max_retries_sets_failed(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_failed(item_id, "err1")
        queue.mark_failed(item_id, "err2")
        item = queue.get_all()[0]
        assert item.status == EmailStatus.FAILED

    def test_failed_item_not_in_pending(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_failed(item_id, "e")
        queue.mark_failed(item_id, "e")
        assert queue.get_pending() == []

    def test_retrying_item_stays_in_pending(self, queue, msg):
        item_id = queue.add(msg)
        queue.mark_failed(item_id, "e")
        pending = queue.get_pending()
        assert len(pending) == 1
        assert pending[0].status == EmailStatus.RETRYING


class TestStats:
    def test_empty_queue(self, queue):
        stats = queue.stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0

    def test_mixed_statuses(self, queue):
        m1 = EmailMessage(to=["a@b.com"], subject="A", body_html="<p/>")
        m2 = EmailMessage(to=["b@c.com"], subject="B", body_html="<p/>")
        m3 = EmailMessage(to=["c@d.com"], subject="C", body_html="<p/>")

        id1 = queue.add(m1)
        id2 = queue.add(m2)
        id3 = queue.add(m3)

        queue.mark_sent(id1)
        queue.mark_failed(id2, "err")
        queue.mark_failed(id2, "err")  # permanently failed

        stats = queue.stats()
        assert stats["total"] == 3
        assert stats["sent"] == 1
        assert stats["failed"] == 1
        assert stats["pending"] == 1


class TestGetAll:
    def test_empty_returns_empty_list(self, queue):
        assert queue.get_all() == []

    def test_message_fields_round_trip(self, queue):
        msg = EmailMessage(
            to=["x@y.com"],
            subject="Round trip",
            body_html="<b>test</b>",
            body_text="test",
            cc=["cc@y.com"],
            bcc=["bcc@y.com"],
        )
        queue.add(msg)
        item = queue.get_all()[0]
        assert item.message.subject == "Round trip"
        assert item.message.cc == ["cc@y.com"]
        assert item.message.bcc == ["bcc@y.com"]
        assert item.message.body_text == "test"
