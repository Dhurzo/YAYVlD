"""Tests for the Typer CLI interface."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner


# Rich formatting in Typer help output adds ANSI escape codes.
ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    return ansi_escape.sub("", text)

from ytpl_dl.cli import app
from ytpl_dl.config import DownloadConfig
from ytpl_dl.errors import PlaylistNotFoundError
from ytpl_dl.playlist import DownloadSummary

runner = CliRunner()

TEST_URL = "https://www.youtube.com/playlist?list=PLtest123"


# ======================================================================
# Test 1: --help output
# ======================================================================


class TestHelp:
    """Verify the --help output shows all options."""

    def test_download_help(self) -> None:
        """Test 1: download --help shows all options with descriptions."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        clean = strip_ansi(result.output)
        assert "playlist_url" in clean
        assert "--output" in clean
        assert "--format" in clean
        assert "--merge-format" in clean
        assert "--concurrent" in clean
        assert "--retries" in clean
        assert "--proxy" in clean
        assert "--no-archive" in clean
        assert "--overwrite" in clean
        assert "--verbose" in clean
        assert "--json-log" in clean


# ======================================================================
# Tests 2-9: Download command with various options
# ======================================================================


class TestDownloadOptions:
    """Verify option values are passed through to DownloadConfig."""

    @pytest.fixture
    def mocks(self, mocker: Any) -> dict[str, MagicMock]:
        """Mock PlaylistDownloader and setup_logging."""
        mock_cls = mocker.patch("ytpl_dl.cli.PlaylistDownloader")
        instance = mock_cls.return_value
        instance.download.return_value = DownloadSummary(
            total=3,
            succeeded=3,
            failed=0,
            skipped=0,
            results=[],
            errors=[],
        )
        mock_logging = mocker.patch("ytpl_dl.cli.setup_logging")
        return {"downloader_cls": mock_cls, "downloader": instance, "logging": mock_logging}

    # --- Test 2: default config ---

    def test_default_config(self, mocks: dict[str, MagicMock]) -> None:
        """Test 2: download <url> invokes PlaylistDownloader with default config."""
        result = runner.invoke(app, [TEST_URL])
        assert result.exit_code == 0

        mocks["downloader_cls"].assert_called_once()
        config: DownloadConfig = mocks["downloader_cls"].call_args[0][0]
        assert isinstance(config, DownloadConfig)
        assert config.output_dir == Path("downloads")
        assert config.format == "bestvideo+bestaudio/best"
        assert config.merge_output_format == "mkv"
        assert config.concurrent_fragments == 8
        assert config.retries == 10
        assert config.overwrite is False
        assert config.proxy is None
        assert config.verbose is False
        # By default download_archive is set to output / ".download_archive"
        assert config.download_archive == Path("downloads") / ".download_archive"

        mocks["downloader"].download.assert_called_once_with(TEST_URL)

        # Summary is printed on completion
        assert "Download Complete" in result.output

    # --- Test 3: custom output directory ---

    def test_custom_output(self, mocks: dict[str, MagicMock]) -> None:
        """Test 3: download <url> -o /custom/dir sets config.output_dir."""
        runner.invoke(app, [TEST_URL, "--output", "/custom/dir"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.output_dir == Path("/custom/dir")

    def test_custom_output_short(self, mocks: dict[str, MagicMock]) -> None:
        """Test 3b: -o short form also works."""
        runner.invoke(app, [TEST_URL, "-o", "/other/path"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.output_dir == Path("/other/path")

    # --- Test 4: custom format ---

    def test_custom_format(self, mocks: dict[str, MagicMock]) -> None:
        """Test 4: download <url> --format 'best' sets config.format."""
        runner.invoke(app, [TEST_URL, "--format", "best"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.format == "best"

    def test_custom_format_short(self, mocks: dict[str, MagicMock]) -> None:
        """Test 4b: -f short form works."""
        runner.invoke(app, [TEST_URL, "-f", "bestaudio"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.format == "bestaudio"

    # --- Test 5: concurrent fragments ---

    def test_concurrent(self, mocks: dict[str, MagicMock]) -> None:
        """Test 5: download <url> --concurrent 4 sets concurrent_fragments."""
        runner.invoke(app, [TEST_URL, "--concurrent", "4"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.concurrent_fragments == 4

    def test_concurrent_short(self, mocks: dict[str, MagicMock]) -> None:
        """Test 5b: -c short form works."""
        runner.invoke(app, [TEST_URL, "-c", "2"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.concurrent_fragments == 2

    # --- Test 6: verbose ---

    def test_verbose(self, mocks: dict[str, MagicMock]) -> None:
        """Test 6: download <url> --verbose enables verbose logging."""
        runner.invoke(app, [TEST_URL, "--verbose"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.verbose is True
        mocks["logging"].assert_called_once_with(verbose=True, json_output=False)

    def test_verbose_short(self, mocks: dict[str, MagicMock]) -> None:
        """Test 6b: -v short form works."""
        runner.invoke(app, [TEST_URL, "-v"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.verbose is True

    # --- Test 7: JSON log ---

    def test_json_log(self, mocks: dict[str, MagicMock]) -> None:
        """Test 7: download <url> --json-log enables JSON output."""
        runner.invoke(app, [TEST_URL, "--json-log"])
        mocks["logging"].assert_called_once_with(verbose=False, json_output=True)

    # --- Test 8: no archive ---

    def test_no_archive(self, mocks: dict[str, MagicMock]) -> None:
        """Test 8: download <url> --no-archive disables download archive."""
        runner.invoke(app, [TEST_URL, "--no-archive"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.download_archive is None

    # --- Test 9: proxy ---

    def test_proxy(self, mocks: dict[str, MagicMock]) -> None:
        """Test 9: download <url> --proxy http://proxy:8080 sets config.proxy."""
        runner.invoke(app, [TEST_URL, "--proxy", "http://proxy:8080"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.proxy == "http://proxy:8080"

    def test_proxy_short(self, mocks: dict[str, MagicMock]) -> None:
        """Test 9b: -p short form works."""
        runner.invoke(app, [TEST_URL, "-p", "http://proxy:3128"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.proxy == "http://proxy:3128"

    # --- Additional: overwrite flag ---

    def test_overwrite(self, mocks: dict[str, MagicMock]) -> None:
        """--overwrite flag sets config.overwrite to True."""
        runner.invoke(app, [TEST_URL, "--overwrite"])
        config = mocks["downloader_cls"].call_args[0][0]
        assert config.overwrite is True


# ======================================================================
# Tests 10-12: Exit codes
# ======================================================================


class TestExitCodes:
    """Verify exit code behavior."""

    @pytest.fixture
    def mock_cls(self, mocker: Any) -> MagicMock:
        """Mock PlaylistDownloader class (no default return value)."""
        return mocker.patch("ytpl_dl.cli.PlaylistDownloader")  # type: ignore[no-any-return]

    # --- Test 11: all succeed → exit code 0 ---

    def test_all_success_exit_code_0(self, mock_cls: MagicMock) -> None:
        """Test 11: All videos succeed → exit code 0."""
        instance = mock_cls.return_value
        instance.download.return_value = DownloadSummary(
            total=3,
            succeeded=3,
            failed=0,
            skipped=0,
            results=[],
            errors=[],
        )
        result = runner.invoke(app, [TEST_URL])
        assert result.exit_code == 0

    # --- Test 12: some failures → exit code 1 ---

    def test_partial_failure_exit_code_1(self, mock_cls: MagicMock) -> None:
        """Test 12: Some videos fail → exit code 1."""
        instance = mock_cls.return_value
        instance.download.return_value = DownloadSummary(
            total=3,
            succeeded=2,
            failed=1,
            skipped=0,
            results=[],
            errors=["HTTP 403"],
        )
        result = runner.invoke(app, [TEST_URL])
        assert result.exit_code == 1
        # Summary should still be printed
        assert "Download Complete" in result.output
        assert "Error" in result.output or "Failed" in result.output

    # --- Test 10: invalid URL → exit code 2 ---

    def test_fatal_error_exit_code_2(self, mock_cls: MagicMock) -> None:
        """Test 10: Fatal error (invalid URL) → exit code 2."""
        instance = mock_cls.return_value
        instance.download.side_effect = PlaylistNotFoundError("Invalid YouTube URL")
        result = runner.invoke(app, [TEST_URL])
        assert result.exit_code == 2
        assert "Error" in result.output
