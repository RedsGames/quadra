"""Tests for the Mailer class using SMTP mocks."""

import smtplib
from unittest.mock import MagicMock, patch, call

import pytest

from src.config import SMTPConfig
from src.mailer import Mailer, MailerError
from src.models import EmailMessage


@pytest.fixture
def smtp_config() -> SMTPConfig:
    return SMTPConfig(
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="s3cr3t",
        use_tls=True,
        sender_name="Test Sender",
        sender_email="user@example.com",
    )


@pytest.fixture
def ssl_config() -> SMTPConfig:
    return SMTPConfig(
        host="smtp.example.com",
        port=465,
        username="user@example.com",
        password="s3cr3t",
        use_tls=False,
        sender_name="Test Sender",
        sender_email="user@example.com",
    )


@pytest.fixture
def message() -> EmailMessage:
    return EmailMessage(
        to=["recipient@example.com"],
        subject="Hello",
        body_html="<p>Hello!</p>",
    )


def _make_smtp_mock():
    """Return a context-manager-aware SMTP mock."""
    mock = MagicMock()
    mock.__enter__ = lambda s: mock
    mock.__exit__ = MagicMock(return_value=False)
    return mock


class TestBuildMime:
    def test_subject_set(self, smtp_config, message):
        mime = Mailer(smtp_config)._build_mime(message)
        assert mime["Subject"] == "Hello"

    def test_to_header(self, smtp_config, message):
        mime = Mailer(smtp_config)._build_mime(message)
        assert "recipient@example.com" in mime["To"]

    def test_from_includes_sender_name(self, smtp_config, message):
        mime = Mailer(smtp_config)._build_mime(message)
        assert "Test Sender" in mime["From"]

    def test_cc_header_present(self, smtp_config):
        msg = EmailMessage(
            to=["a@b.com"], cc=["cc@b.com"], subject="S", body_html="<p/>"
        )
        mime = Mailer(smtp_config)._build_mime(msg)
        assert "cc@b.com" in mime["Cc"]

    def test_no_cc_header_when_empty(self, smtp_config, message):
        mime = Mailer(smtp_config)._build_mime(message)
        assert mime["Cc"] is None

    def test_plain_text_part_attached_when_provided(self, smtp_config):
        msg = EmailMessage(
            to=["a@b.com"], subject="S", body_html="<p/>", body_text="plain text"
        )
        mime = Mailer(smtp_config)._build_mime(msg)
        payloads = [p.get_payload(decode=True).decode() for p in mime.get_payload()]
        assert any("plain text" in p for p in payloads)


class TestSendSuccess:
    def test_tls_path_calls_starttls(self, smtp_config, message):
        mock_smtp = _make_smtp_mock()
        with patch("smtplib.SMTP", return_value=mock_smtp):
            Mailer(smtp_config).send(message)
        mock_smtp.starttls.assert_called_once()

    def test_login_called(self, smtp_config, message):
        mock_smtp = _make_smtp_mock()
        with patch("smtplib.SMTP", return_value=mock_smtp):
            Mailer(smtp_config).send(message)
        mock_smtp.login.assert_called_once_with("user@example.com", "s3cr3t")

    def test_sendmail_called_with_correct_sender(self, smtp_config, message):
        mock_smtp = _make_smtp_mock()
        with patch("smtplib.SMTP", return_value=mock_smtp):
            Mailer(smtp_config).send(message)
        args = mock_smtp.sendmail.call_args
        assert args[0][0] == "user@example.com"

    def test_sendmail_includes_all_recipients(self, smtp_config):
        msg = EmailMessage(
            to=["a@b.com"],
            cc=["c@d.com"],
            bcc=["e@f.com"],
            subject="S",
            body_html="<p/>",
        )
        mock_smtp = _make_smtp_mock()
        with patch("smtplib.SMTP", return_value=mock_smtp):
            Mailer(smtp_config).send(msg)
        recipients = mock_smtp.sendmail.call_args[0][1]
        assert set(recipients) == {"a@b.com", "c@d.com", "e@f.com"}

    def test_ssl_path_uses_smtp_ssl(self, ssl_config, message):
        mock_smtp = _make_smtp_mock()
        with patch("smtplib.SMTP_SSL", return_value=mock_smtp) as mock_cls:
            Mailer(ssl_config).send(message)
        mock_cls.assert_called_once()
        mock_smtp.starttls.assert_not_called()


class TestSendErrors:
    def test_auth_failure_raises_mailer_error(self, smtp_config, message):
        mock_smtp = _make_smtp_mock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad creds")
        with patch("smtplib.SMTP", return_value=mock_smtp):
            with pytest.raises(MailerError, match="authentication"):
                Mailer(smtp_config).send(message)

    def test_connection_error_raises_mailer_error(self, smtp_config, message):
        with patch("smtplib.SMTP", side_effect=OSError("Connection refused")):
            with pytest.raises(MailerError, match="Connection error"):
                Mailer(smtp_config).send(message)

    def test_smtp_exception_raises_mailer_error(self, smtp_config, message):
        mock_smtp = _make_smtp_mock()
        mock_smtp.sendmail.side_effect = smtplib.SMTPException("Unknown error")
        with patch("smtplib.SMTP", return_value=mock_smtp):
            with pytest.raises(MailerError, match="SMTP error"):
                Mailer(smtp_config).send(message)

    def test_recipients_refused_raises_mailer_error(self, smtp_config, message):
        mock_smtp = _make_smtp_mock()
        mock_smtp.sendmail.side_effect = smtplib.SMTPRecipientsRefused(
            {"bad@bad.com": (550, b"No such user")}
        )
        with patch("smtplib.SMTP", return_value=mock_smtp):
            with pytest.raises(MailerError, match="refused"):
                Mailer(smtp_config).send(message)
