"""Configuration management.

Values are read from a config.ini file; environment variables
take precedence so that secrets can be injected without touching
the file on disk.
"""

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SMTPConfig:
    """SMTP connection and sender settings."""

    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    sender_name: str
    sender_email: str


@dataclass
class AppConfig:
    """Top-level application configuration."""

    smtp: SMTPConfig
    queue_file: Path
    templates_dir: Path
    log_file: Path
    max_retries: int
    retry_delay: int  # seconds between automatic retries


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load and merge configuration from *config_path* and environment variables.

    Environment variables always override file values.  Missing keys fall back
    to sensible defaults so the application can start without a config file.

    Args:
        config_path: Explicit path to a config.ini file.  Defaults to
            ``<project_root>/config.ini``.

    Returns:
        Fully populated :class:`AppConfig` instance.
    """
    parser = configparser.ConfigParser()

    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.ini"

    parser.read(str(config_path), encoding="utf-8")

    def _get(section: str, key: str, fallback: str = "") -> str:
        return parser.get(section, key, fallback=fallback)

    smtp = SMTPConfig(
        host=os.getenv("SMTP_HOST", _get("smtp", "host", "smtp.gmail.com")),
        port=int(os.getenv("SMTP_PORT", _get("smtp", "port", "587"))),
        username=os.getenv("SMTP_USERNAME", _get("smtp", "username", "")),
        password=os.getenv("SMTP_PASSWORD", _get("smtp", "password", "")),
        use_tls=os.getenv("SMTP_TLS", _get("smtp", "use_tls", "true")).lower() == "true",
        sender_name=os.getenv("SENDER_NAME", _get("smtp", "sender_name", "Auto Reporter")),
        sender_email=os.getenv("SENDER_EMAIL", _get("smtp", "sender_email", "")),
    )

    base_dir = Path(__file__).parent.parent

    return AppConfig(
        smtp=smtp,
        queue_file=Path(
            os.getenv(
                "QUEUE_FILE", _get("app", "queue_file", str(base_dir / "data" / "queue.json"))
            )
        ),
        templates_dir=Path(
            os.getenv("TEMPLATES_DIR", _get("app", "templates_dir", str(base_dir / "templates")))
        ),
        log_file=Path(
            os.getenv("LOG_FILE", _get("app", "log_file", str(base_dir / "logs" / "app.log")))
        ),
        max_retries=int(os.getenv("MAX_RETRIES", _get("app", "max_retries", "3"))),
        retry_delay=int(os.getenv("RETRY_DELAY", _get("app", "retry_delay", "60"))),
    )
