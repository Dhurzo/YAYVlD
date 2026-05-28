"""Tests for VideoDownloader with mocked yt-dlp."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from yt_dlp.utils import (
    DownloadError,
    ExtractorError,
)
from yt_dlp.utils import (
    GeoRestrictedError as YtdlpGeoError,
)

from ytpl_dl.config import DownloadConfig
from ytpl_dl.downloader import VideoDownloader
from ytpl_dl.errors import (
    AgeRestrictedError,
    GeoRestrictedError,
    VideoUnavailableError,
)
from ytpl_dl.models import DownloadResult, VideoInfo


@pytest.fixture
def mock_ydl(mocker):
    mock_instance = mocker.MagicMock()
    mocker.patch("ytpl_dl.downloader.yt_dlp.YoutubeDL", return_value=mock_instance)
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)
    return mock_instance


@pytest.fixture
def default_config(tmp_path):
    return DownloadConfig(output_dir=tmp_path)


@pytest.fixture
def downloader(default_config):
    return VideoDownloader(config=default_config)


class TestDownloadHappyPath:
    def test_success_returns_download_result(self, mock_ydl, downloader, sample_video, tmp_path):
        expected_path = str(tmp_path / "Rick Astley [dQw4w9WgXcQ].mkv")
        mock_ydl.download.return_value = 0
        mock_ydl.prepare_filename.return_value = expected_path

        result = downloader.download(sample_video)

        assert isinstance(result, DownloadResult)
        assert result.success is True
        assert result.file_path == Path(expected_path)
        assert result.error is None
        assert result.video == sample_video
        mock_ydl.download.assert_called_once_with([sample_video.url])


class TestDownloadError:
    def test_download_error_returns_failure(self, mock_ydl, downloader, sample_video):
        mock_ydl.download.side_effect = DownloadError("HTTP Error 403: Forbidden")

        result = downloader.download(sample_video)

        assert result.success is False
        assert result.error is not None
        assert "403" in result.error


class TestGeoRestricted:
    def test_geo_restricted_error_translated(self, mock_ydl, downloader, sample_video):
        mock_ydl.download.side_effect = YtdlpGeoError(
            "The uploader has not made this video available in your country"
        )

        result = downloader.download(sample_video)

        assert result.success is False
        assert result.error is not None

        domain_error = downloader._translate_error(YtdlpGeoError("geo blocked"))
        assert isinstance(domain_error, GeoRestrictedError)


class TestAgeRestricted:
    def test_age_restricted_error_translated(self, mock_ydl, downloader, sample_video):
        mock_ydl.download.side_effect = ExtractorError(
            "Sign in to confirm your age", video_id="dQw4w9WgXcQ"
        )

        result = downloader.download(sample_video)

        assert result.success is False
        assert result.error is not None

        domain_error = downloader._translate_error(ExtractorError("Sign in to confirm your age"))
        assert isinstance(domain_error, AgeRestrictedError)


class TestUnavailable:
    def test_private_video_translated(self, mock_ydl, downloader, sample_video):
        mock_ydl.download.side_effect = ExtractorError("Private video", video_id="dQw4w9WgXcQ")

        result = downloader.download(sample_video)
        assert result.success is False

        domain_error = downloader._translate_error(ExtractorError("Private video"))
        assert isinstance(domain_error, VideoUnavailableError)

    def test_deleted_video_translated(self, downloader):
        domain_error = downloader._translate_error(ExtractorError("Video unavailable"))
        assert isinstance(domain_error, VideoUnavailableError)


class TestProgressCallback:
    def test_progress_callback_wired_to_hooks(self, mocker, tmp_path, sample_video):
        callback = mocker.MagicMock()
        config = DownloadConfig(output_dir=tmp_path)

        mock_instance = mocker.MagicMock()
        mock_class = mocker.patch(
            "ytpl_dl.downloader.yt_dlp.YoutubeDL",
            return_value=mock_instance,
        )
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.download.return_value = 0
        mock_instance.prepare_filename.return_value = str(tmp_path / "out.mkv")

        dl = VideoDownloader(config=config, progress_callback=callback)
        result = dl.download(sample_video)

        assert result.success is True

        opts = mock_class.call_args[0][0]
        assert "progress_hooks" in opts
        assert len(opts["progress_hooks"]) == 1

        hook = opts["progress_hooks"][0]
        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes": 100,
                "speed": 1000.0,
                "eta": 5.0,
                "filename": "video.mkv",
            }
        )
        callback.assert_called_once()


class TestArchivePath:
    def test_archive_path_in_opts_when_set(self, tmp_path, sample_video):
        """When archive_path is set, download_archive must be in yt-dlp opts."""
        config = DownloadConfig(output_dir=tmp_path, download_archive=tmp_path / ".archive")
        dl = VideoDownloader(config=config)
        opts = dl._build_ydl_opts(sample_video)

        assert "download_archive" in opts
        assert opts["download_archive"] == str(tmp_path / ".archive")

    def test_archive_path_absent_when_none(self, downloader, sample_video):
        """When archive_path is None, download_archive must NOT be in yt-dlp opts."""
        opts = downloader._build_ydl_opts(sample_video)

        assert "download_archive" not in opts


class TestProxyOption:
    def test_proxy_set_in_opts(self, tmp_path):
        config = DownloadConfig(output_dir=tmp_path, proxy="http://proxy:8080")
        dl = VideoDownloader(config=config)
        video = VideoInfo(id="abc", title="T", url="https://youtube.com/watch?v=abc")

        opts = dl._build_ydl_opts(video)

        assert "proxy" in opts
        assert opts["proxy"] == "http://proxy:8080"

    def test_proxy_absent_when_none(self, tmp_path):
        config = DownloadConfig(output_dir=tmp_path)
        dl = VideoDownloader(config=config)
        video = VideoInfo(id="abc", title="T", url="https://youtube.com/watch?v=abc")

        opts = dl._build_ydl_opts(video)

        assert "proxy" not in opts


class TestOutputTemplate:
    def test_outtmpl_includes_id_and_title(self, downloader, sample_video):
        opts = downloader._build_ydl_opts(sample_video)

        assert "outtmpl" in opts
        outtmpl = opts["outtmpl"]
        assert "%(id)s" in outtmpl
        assert "%(title)" in outtmpl
        assert "%(ext)s" in outtmpl
        assert "001 -" in outtmpl  # Check for padded index (default 001 for index=1)
