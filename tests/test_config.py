"""Tests for DownloadConfig validation in ytpl_dl.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from ytpl_dl.config import DownloadConfig
from ytpl_dl.errors import ConfigValidationError


class TestDownloadConfigDefaults:
    def test_default_creation(self) -> None:
        cfg = DownloadConfig()
        assert cfg.output_dir == Path("downloads")
        assert cfg.format == "bestvideo+bestaudio/best"
        assert cfg.merge_output_format == "mkv"
        assert cfg.concurrent_fragments == 8
        assert cfg.retries == 10
        assert cfg.fragment_retries == 10
        assert cfg.timeout == 30
        assert cfg.download_archive is None
        assert cfg.overwrite is False
        assert cfg.proxy is None
        assert cfg.verbose is False


class TestDownloadConfigValidation:
    def test_concurrent_fragments_zero(self) -> None:
        with pytest.raises(ConfigValidationError, match="concurrent_fragments"):
            DownloadConfig(concurrent_fragments=0)

    def test_concurrent_fragments_seventeen(self) -> None:
        with pytest.raises(ConfigValidationError, match="concurrent_fragments"):
            DownloadConfig(concurrent_fragments=17)

    def test_concurrent_fragments_boundary_min(self) -> None:
        cfg = DownloadConfig(concurrent_fragments=1)
        assert cfg.concurrent_fragments == 1

    def test_concurrent_fragments_boundary_max(self) -> None:
        cfg = DownloadConfig(concurrent_fragments=16)
        assert cfg.concurrent_fragments == 16

    def test_retries_negative(self) -> None:
        with pytest.raises(ConfigValidationError, match="retries"):
            DownloadConfig(retries=-1)

    def test_retries_zero_valid(self) -> None:
        cfg = DownloadConfig(retries=0)
        assert cfg.retries == 0

    def test_fragment_retries_negative(self) -> None:
        with pytest.raises(ConfigValidationError, match="fragment_retries"):
            DownloadConfig(fragment_retries=-1)

    def test_fragment_retries_zero_valid(self) -> None:
        cfg = DownloadConfig(fragment_retries=0)
        assert cfg.fragment_retries == 0

    def test_timeout_zero(self) -> None:
        with pytest.raises(ConfigValidationError, match="timeout"):
            DownloadConfig(timeout=0)

    def test_timeout_one_valid(self) -> None:
        cfg = DownloadConfig(timeout=1)
        assert cfg.timeout == 1


class TestArchivePath:
    def test_archive_path_none_by_default(self) -> None:
        """archive_path is None when no download_archive is configured."""
        cfg = DownloadConfig(output_dir=Path("/tmp/downloads"))
        assert cfg.archive_path is None

    def test_explicit_archive_path(self) -> None:
        """archive_path returns the explicitly set download_archive."""
        explicit = Path("/custom/archive.txt")
        cfg = DownloadConfig(download_archive=explicit)
        assert cfg.archive_path == explicit


class TestCustomOutputDir:
    def test_custom_output_dir(self) -> None:
        cfg = DownloadConfig(output_dir=Path("/media/videos"))
        assert cfg.output_dir == Path("/media/videos")

    def test_frozen(self) -> None:
        cfg = DownloadConfig()
        with pytest.raises(AttributeError):
            cfg.timeout = 99  # type: ignore[misc]
