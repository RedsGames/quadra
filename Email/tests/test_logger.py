"""Tests for the logger setup utility."""

import logging
from pathlib import Path

import pytest

from src.logger import setup_logger


@pytest.fixture(autouse=True)
def reset_logger():
    """Clear email_sender handlers before/after each test for isolation."""
    lg = logging.getLogger("email_sender")
    lg.handlers.clear()
    yield
    for h in lg.handlers[:]:
        h.close()
    lg.handlers.clear()


class TestSetupLogger:
    def test_returns_logger_instance(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger(log_file)
        assert isinstance(logger, logging.Logger)

    def test_log_file_created(self, tmp_path):
        log_file = tmp_path / "subdir" / "app.log"
        logger = setup_logger(log_file)
        logger.info("test message")
        assert log_file.exists()

    def test_log_directory_created_automatically(self, tmp_path):
        log_file = tmp_path / "a" / "b" / "c" / "app.log"
        setup_logger(log_file)
        assert log_file.parent.exists()

    def test_logger_name(self, tmp_path):
        log_file = tmp_path / "app.log"
        logger = setup_logger(log_file)
        assert logger.name == "email_sender"

    def test_second_call_does_not_duplicate_handlers(self, tmp_path):
        log_file = tmp_path / "app.log"
        # Reset handlers to ensure clean state for this test
        logging.getLogger("email_sender").handlers.clear()
        setup_logger(log_file)
        handler_count_after_first = len(logging.getLogger("email_sender").handlers)
        setup_logger(log_file)
        handler_count_after_second = len(logging.getLogger("email_sender").handlers)
        assert handler_count_after_first == handler_count_after_second

    def test_message_written_to_file(self, tmp_path):
        log_file = tmp_path / "app.log"
        logging.getLogger("email_sender").handlers.clear()
        logger = setup_logger(log_file)
        logger.info("hello from test")
        content = log_file.read_text(encoding="utf-8")
        assert "hello from test" in content
