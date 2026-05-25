"""SMTP email delivery using the standard library :mod:`smtplib`."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import List

from .config import SMTPConfig
from .models import EmailMessage

logger = logging.getLogger("email_sender.mailer")


class MailerError(Exception):
    """Raised when an email cannot be delivered."""


class Mailer:
    """Sends :class:`~src.models.EmailMessage` objects via SMTP.

    Supports both STARTTLS (port 587) and implicit TLS/SSL (port 465).

    Args:
        config: SMTP connection and sender settings.
    """

    def __init__(self, config: SMTPConfig) -> None:
        self._config = config

    def _build_mime(self, message: EmailMessage) -> MIMEMultipart:
        """Construct a MIME multipart message from an :class:`EmailMessage`.

        Attaches a plain-text fallback part when :attr:`~EmailMessage.body_text`
        is provided, followed by the HTML part.
        """
        mime = MIMEMultipart("alternative")
        mime["Subject"] = message.subject
        mime["From"] = formataddr((self._config.sender_name, self._config.sender_email))
        mime["To"] = ", ".join(message.to)

        if message.cc:
            mime["Cc"] = ", ".join(message.cc)

        if message.body_text:
            mime.attach(MIMEText(message.body_text, "plain", "utf-8"))

        mime.attach(MIMEText(message.body_html, "html", "utf-8"))
        return mime

    def _all_recipients(self, message: EmailMessage) -> List[str]:
        return message.to + message.cc + message.bcc

    def send(self, message: EmailMessage) -> None:
        """Send *message* via SMTP.

        Args:
            message: Email to deliver.

        Raises:
            MailerError: On authentication failure, SMTP protocol error,
                or network connectivity problem.
        """
        mime = self._build_mime(message)
        recipients = self._all_recipients(message)

        try:
            if self._config.use_tls:
                smtp = smtplib.SMTP(self._config.host, self._config.port, timeout=30)
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
            else:
                smtp = smtplib.SMTP_SSL(self._config.host, self._config.port, timeout=30)

            with smtp:
                smtp.login(self._config.username, self._config.password)
                smtp.sendmail(
                    self._config.sender_email,
                    recipients,
                    mime.as_bytes(),
                )

        except smtplib.SMTPAuthenticationError as exc:
            raise MailerError("SMTP authentication failed — check username/password") from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise MailerError(f"All recipients refused: {exc.recipients}") from exc
        except smtplib.SMTPException as exc:
            raise MailerError(f"SMTP error: {exc}") from exc
        except OSError as exc:
            raise MailerError(f"Connection error: {exc}") from exc

        logger.info(
            "Delivered '%s' to %s",
            message.subject,
            ", ".join(recipients),
        )
