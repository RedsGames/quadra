"""Tests for data models."""

import pytest
from src.models import EmailMessage, EmailStatus, QueueItem


class TestEmailMessage:
    def test_single_string_to_becomes_list(self):
        msg = EmailMessage(to="a@b.com", subject="S", body_html="<p/>")
        assert isinstance(msg.to, list)
        assert msg.to == ["a@b.com"]

    def test_list_to_stays_list(self):
        msg = EmailMessage(to=["a@b.com", "c@d.com"], subject="S", body_html="<p/>")
        assert len(msg.to) == 2

    def test_cc_bcc_default_empty(self):
        msg = EmailMessage(to=["a@b.com"], subject="S", body_html="<p/>")
        assert msg.cc == []
        assert msg.bcc == []

    def test_string_cc_becomes_list(self):
        msg = EmailMessage(to=["a@b.com"], subject="S", body_html="<p/>", cc="x@y.com")
        assert isinstance(msg.cc, list)

    def test_body_text_optional(self):
        msg = EmailMessage(to=["a@b.com"], subject="S", body_html="<p/>")
        assert msg.body_text is None


class TestEmailStatus:
    def test_values(self):
        assert EmailStatus.PENDING == "pending"
        assert EmailStatus.SENT == "sent"
        assert EmailStatus.FAILED == "failed"
        assert EmailStatus.RETRYING == "retrying"


class TestQueueItem:
    def test_default_status_is_pending(self):
        msg = EmailMessage(to=["a@b.com"], subject="S", body_html="<p/>")
        item = QueueItem(message=msg, item_id="abc-123")
        assert item.status == EmailStatus.PENDING

    def test_retries_start_at_zero(self):
        msg = EmailMessage(to=["a@b.com"], subject="S", body_html="<p/>")
        item = QueueItem(message=msg, item_id="abc-123")
        assert item.retries == 0

    def test_created_at_is_set_automatically(self):
        msg = EmailMessage(to=["a@b.com"], subject="S", body_html="<p/>")
        item = QueueItem(message=msg, item_id="abc-123")
        assert item.created_at is not None and "T" in item.created_at
