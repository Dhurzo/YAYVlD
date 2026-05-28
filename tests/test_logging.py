"""Tests for logging setup in ytpl_dl.logging."""

from __future__ import annotations

import logging

from ytpl_dl.logging import get_logger, setup_logging


class TestSetupLogging:
    def test_default_setup_no_error(self) -> None:
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_verbose_enables_debug(self) -> None:
        setup_logging(verbose=True)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_json_output_no_error(self) -> None:
        setup_logging(json_output=True)
        root = logging.getLogger()
        assert root.level == logging.INFO


class TestGetLogger:
    def test_returns_bound_logger(self) -> None:
        setup_logging()
        logger = get_logger()
        assert logger is not None

    def test_with_name(self) -> None:
        setup_logging()
        logger = get_logger("test")
        assert logger is not None
