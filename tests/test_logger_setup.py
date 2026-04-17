"""Tests for logging setup helpers."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from utils.logger import LoggerWriter, setup_logging


def _remove_new_handlers(logger: logging.Logger, baseline: list[logging.Handler]) -> None:
    for handler in list(logger.handlers):
        if handler not in baseline:
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass


def test_setup_logging_redirects_streams_and_writes_log(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    root_logger = logging.getLogger()
    app_logger = logging.getLogger("AppLogger")
    root_handlers_before = list(root_logger.handlers)
    app_handlers_before = list(app_logger.handlers)

    try:
        setup_logging(str(log_file), max_bytes=4096, backup_count=1)

        assert isinstance(sys.stdout, LoggerWriter)
        assert isinstance(sys.stderr, LoggerWriter)

        print("stdout-marker")
        sys.stderr.write("stderr-marker\n")
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        _remove_new_handlers(root_logger, root_handlers_before)
        _remove_new_handlers(app_logger, app_handlers_before)

    content = log_file.read_text(encoding="utf-8")
    assert "stdout-marker" in content
    assert "stderr-marker" in content


def test_setup_logging_respects_environment_log_level(monkeypatch, tmp_path: Path) -> None:
    log_file = tmp_path / "env.log"
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    root_logger = logging.getLogger()
    app_logger = logging.getLogger("AppLogger")
    root_handlers_before = list(root_logger.handlers)
    app_handlers_before = list(app_logger.handlers)
    level_before = root_logger.level

    try:
        monkeypatch.setenv("ISOTOPES_LOG_LEVEL", "INFO")
        setup_logging(str(log_file), max_bytes=4096, backup_count=1)

        assert root_logger.level == logging.INFO
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        root_logger.setLevel(level_before)
        _remove_new_handlers(root_logger, root_handlers_before)
        _remove_new_handlers(app_logger, app_handlers_before)
