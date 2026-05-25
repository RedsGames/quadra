"""Tests for configuration loading."""

import os
from pathlib import Path

import pytest

from src.config import load_config


def _write_config(tmp_path: Path, extra: str = "") -> Path:
    cfg = tmp_path / "config.ini"
    cfg.write_text(
        "[smtp]\n"
        "host = mail.example.com\n"
        "port = 465\n"
        "username = test@example.com\n"
        "password = secret\n"
        "use_tls = false\n"
        "sender_name = Tester\n"
        "sender_email = test@example.com\n"
        "[app]\n"
        f"queue_file = {tmp_path / 'queue.json'}\n"
        f"templates_dir = {tmp_path / 'templates'}\n"
        f"log_file = {tmp_path / 'app.log'}\n"
        "max_retries = 5\n"
        "retry_delay = 30\n"
        + extra,
        encoding="utf-8",
    )
    return cfg


class TestLoadConfig:
    def test_reads_smtp_host(self, tmp_path):
        cfg = _write_config(tmp_path)
        config = load_config(str(cfg))
        assert config.smtp.host == "mail.example.com"

    def test_reads_smtp_port_as_int(self, tmp_path):
        cfg = _write_config(tmp_path)
        config = load_config(str(cfg))
        assert config.smtp.port == 465

    def test_use_tls_false(self, tmp_path):
        cfg = _write_config(tmp_path)
        config = load_config(str(cfg))
        assert config.smtp.use_tls is False

    def test_max_retries(self, tmp_path):
        cfg = _write_config(tmp_path)
        config = load_config(str(cfg))
        assert config.max_retries == 5

    def test_env_overrides_smtp_host(self, tmp_path, monkeypatch):
        cfg = _write_config(tmp_path)
        monkeypatch.setenv("SMTP_HOST", "override.host")
        config = load_config(str(cfg))
        assert config.smtp.host == "override.host"

    def test_env_overrides_max_retries(self, tmp_path, monkeypatch):
        cfg = _write_config(tmp_path)
        monkeypatch.setenv("MAX_RETRIES", "9")
        config = load_config(str(cfg))
        assert config.max_retries == 9

    def test_missing_file_falls_back_to_defaults(self):
        config = load_config("/nonexistent/path/config.ini")
        assert config.smtp.host == "smtp.gmail.com"
        assert config.smtp.port == 587
        assert config.max_retries == 3

    def test_use_tls_true_from_env(self, tmp_path, monkeypatch):
        cfg = _write_config(tmp_path)
        monkeypatch.setenv("SMTP_TLS", "TRUE")
        config = load_config(str(cfg))
        assert config.smtp.use_tls is True

    def test_queue_file_is_path_instance(self, tmp_path):
        cfg = _write_config(tmp_path)
        config = load_config(str(cfg))
        assert isinstance(config.queue_file, Path)
