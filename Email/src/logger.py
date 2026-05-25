"""Logging configuration for the email auto-sender."""

import logging
import logging.handlers
from pathlib import Path


def setup_logger(log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure and return the application-wide logger.

    Creates the log directory if it does not exist.  Uses a rotating file
    handler (max 5 MB, 3 backups) and a console handler that only emits
    WARNING and above.

    Args:
        log_file: Absolute path to the log file.
        level: Minimum severity level for the file handler.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("email_sender")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
