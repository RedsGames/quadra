"""Тесты для email-модуля (SMTP мокируется — реальных писем не отправляем)."""
import pytest
from unittest.mock import patch, MagicMock
from src.email_module.mailer import Mailer


@pytest.fixture
def mailer():
    return Mailer(
        host="smtp.example.com",
        port=465,
        username="test@example.com",
        password="secret",
        sender_name="Test",
        sender_email="test@example.com",
    )


def test_send_calls_smtp_ssl(mailer):
    with patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_server = MagicMock()
        mock_ssl.return_value.__enter__ = lambda s: mock_server
        mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

        mailer.send("user@example.com", "Тема", "<p>Тело</p>")

        mock_ssl.assert_called_once_with("smtp.example.com", 465)


def test_send_calls_login(mailer):
    with patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_server = MagicMock()
        mock_ssl.return_value.__enter__ = lambda s: mock_server
        mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

        mailer.send("user@example.com", "Тема", "<p>Тело</p>")

        mock_server.login.assert_called_once_with("test@example.com", "secret")


def test_send_calls_sendmail(mailer):
    with patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_server = MagicMock()
        mock_ssl.return_value.__enter__ = lambda s: mock_server
        mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

        mailer.send("user@example.com", "Тема", "<p>Тело</p>")

        assert mock_server.sendmail.called
        args = mock_server.sendmail.call_args[0]
        assert args[0] == "test@example.com"   # от кого
        assert args[1] == "user@example.com"   # кому


def test_send_raises_on_smtp_error(mailer):
    import smtplib
    with patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_ssl.return_value.__enter__ = lambda s: mock_server
        mock_ssl.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(smtplib.SMTPAuthenticationError):
            mailer.send("user@example.com", "Тема", "Тело")
