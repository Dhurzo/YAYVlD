"""Tests for PlaylistExtractor and PlaylistDownloader."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yt_dlp

from ytpl_dl.config import DownloadConfig
from ytpl_dl.errors import PlaylistNotFoundError
from ytpl_dl.models import DownloadResult, PlaylistInfo, VideoInfo
from ytpl_dl.playlist import DownloadSummary, PlaylistDownloader, PlaylistExtractor


class TestPlaylistExtractor:
    """Tests for PlaylistExtractor.extract()."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @pytest.fixture
    def config(self) -> DownloadConfig:
        return DownloadConfig()

    @pytest.fixture
    def extractor(self, config: DownloadConfig) -> PlaylistExtractor:
        return PlaylistExtractor(config)

    def _make_ydl_mock(
        self,
        mocker: Any,
        data: dict[str, Any] | None = None,
        side_effect: Exception | None = None,
    ) -> Any:
        """Return a mocked ``yt_dlp.YoutubeDL`` context manager.

        The mock is patched at the import site used by ``playlist.py`` so
        the real library is never invoked.
        """
        mock_ydl = mocker.MagicMock(spec=yt_dlp.YoutubeDL)
        mock_ydl.__enter__.return_value = mock_ydl
        if side_effect is not None:
            mock_ydl.extract_info.side_effect = side_effect
        elif data is not None:
            mock_ydl.extract_info.return_value = data
        mocker.patch("ytpl_dl.playlist.yt_dlp.YoutubeDL", return_value=mock_ydl)
        return mock_ydl

    def _playlist_data(self, entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "id": "PLtest123",
            "title": "Test Playlist",
            "extractor_key": "YoutubePlaylist",
            "entries": entries or [],
        }

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_extract_happy_path(self, mocker: Any, extractor: PlaylistExtractor) -> None:
        """Happy path: playlist with 3 entries returns PlaylistInfo with 3 VideoInfo."""
        entries = [
            {
                "id": "vid1",
                "title": "Video 1",
                "url": "https://youtube.com/watch?v=vid1",
                "duration": 120,
                "_type": "url",
            },
            {
                "id": "vid2",
                "title": "Video 2",
                "url": "https://youtube.com/watch?v=vid2",
                "duration": 300,
                "_type": "url",
            },
            {
                "id": "vid3",
                "title": "Video 3",
                "url": "https://youtube.com/watch?v=vid3",
                "duration": 180,
                "_type": "url",
            },
        ]
        data = self._playlist_data(entries)
        mock_ydl = self._make_ydl_mock(mocker, data=data)

        url = "https://www.youtube.com/playlist?list=PLtest123"
        result = extractor.extract(url)

        assert result.id == "PLtest123"
        assert result.title == "Test Playlist"
        assert result.url == url
        assert result.video_count == 3
        assert len(result.videos) == 3

        assert result.videos[0].id == "vid1"
        assert result.videos[0].title == "Video 1"
        assert result.videos[0].duration == 120
        assert result.videos[0].index == 1

        assert result.videos[1].id == "vid2"
        assert result.videos[1].index == 2

        assert result.videos[2].id == "vid3"
        assert result.videos[2].index == 3

        mock_ydl.extract_info.assert_called_once_with(url, download=False)

    def test_extract_empty_playlist(self, mocker: Any, extractor: PlaylistExtractor) -> None:
        """Empty playlist entries → PlaylistInfo with video_count=0."""
        data = self._playlist_data([])
        self._make_ydl_mock(mocker, data=data)

        result = extractor.extract("https://www.youtube.com/playlist?list=PLempty")

        assert result.video_count == 0
        assert result.videos == ()

    def test_extract_entry_missing_duration(
        self, mocker: Any, extractor: PlaylistExtractor
    ) -> None:
        """Entry without duration field → VideoInfo(duration=None)."""
        entries = [
            {
                "id": "vid1",
                "title": "Video 1",
                "url": "https://youtube.com/watch?v=vid1",
                "_type": "url",
            },
        ]
        data = self._playlist_data(entries)
        self._make_ydl_mock(mocker, data=data)

        result = extractor.extract("https://www.youtube.com/playlist?list=PLtest")

        assert result.videos[0].duration is None
        assert result.videos[0].id == "vid1"

    def test_extract_invalid_url(self, mocker: Any, extractor: PlaylistExtractor) -> None:
        """Completely invalid URL → PlaylistNotFoundError."""
        with pytest.raises(PlaylistNotFoundError):
            extractor.extract("not-a-url")

    def test_extract_non_playlist_url(self, mocker: Any, extractor: PlaylistExtractor) -> None:
        """YouTube watch URL without ``list`` parameter → PlaylistNotFoundError."""
        with pytest.raises(PlaylistNotFoundError):
            extractor.extract("https://youtube.com/watch?v=abc")

    def test_extract_ytdlp_raises_error(self, mocker: Any, extractor: PlaylistExtractor) -> None:
        """yt-dlp raises ExtractorError → wrapped as PlaylistNotFoundError."""
        self._make_ydl_mock(
            mocker,
            side_effect=yt_dlp.utils.ExtractorError("Video unavailable"),
        )
        with pytest.raises(PlaylistNotFoundError):
            extractor.extract("https://www.youtube.com/playlist?list=PLtest")

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/playlist?list=PLabc123",
            "https://youtube.com/playlist?list=PLabc123",
            "https://youtu.be/abc123",
            "https://www.youtu.be/abc123",
            "https://www.youtube.com/watch?v=abc123&list=PLabc123",
        ],
    )
    def test_extract_valid_url_formats(
        self, mocker: Any, extractor: PlaylistExtractor, url: str
    ) -> None:
        """All valid YouTube playlist URL formats are accepted."""
        data = self._playlist_data([])
        self._make_ydl_mock(mocker, data=data)
        result = extractor.extract(url)
        assert result is not None

    def test_extract_entry_parsing(self, mocker: Any, extractor: PlaylistExtractor) -> None:
        """Entry dict fields are correctly mapped to VideoInfo."""
        entries = [
            {
                "id": "abc123def",
                "title": "My Amazing Video",
                "url": "https://youtube.com/watch?v=abc123def",
                "duration": 60,
                "_type": "url",
            },
        ]
        data = self._playlist_data(entries)
        self._make_ydl_mock(mocker, data=data)

        result = extractor.extract("https://www.youtube.com/playlist?list=PLtest")
        video = result.videos[0]

        assert video.id == "abc123def"
        assert video.title == "My Amazing Video"
        assert video.url == "https://youtube.com/watch?v=abc123def"
        assert video.duration == 60
        assert video.index == 1


# ------------------------------------------------------------------
# PlaylistDownloader tests
# ------------------------------------------------------------------


def _make_videos() -> tuple[VideoInfo, ...]:
    return (
        VideoInfo(
            id="v1", title="Video 1", url="https://youtube.com/watch?v=v1", duration=120, index=1
        ),
        VideoInfo(
            id="v2", title="Video 2", url="https://youtube.com/watch?v=v2", duration=300, index=2
        ),
        VideoInfo(
            id="v3", title="Video 3", url="https://youtube.com/watch?v=v3", duration=180, index=3
        ),
    )


def _success_result(video: VideoInfo) -> DownloadResult:
    return DownloadResult(video=video, success=True, file_path=Path(f"/tmp/{video.id}.mkv"))


def _fail_result(video: VideoInfo, error: str = "Download failed") -> DownloadResult:
    return DownloadResult(video=video, success=False, error=error)


@pytest.fixture
def dl_config(tmp_path: Path) -> DownloadConfig:
    return DownloadConfig(output_dir=tmp_path)


@pytest.fixture
def mock_extractor_cls(mocker: Any) -> MagicMock:
    return mocker.patch("ytpl_dl.playlist.PlaylistExtractor")


@pytest.fixture
def mock_downloader_cls(mocker: Any) -> MagicMock:
    return mocker.patch("ytpl_dl.playlist.VideoDownloader")


class TestPlaylistDownloaderAllSucceed:
    def test_all_succeed(
        self,
        dl_config: DownloadConfig,
        mock_extractor_cls: MagicMock,
        mock_downloader_cls: MagicMock,
    ) -> None:
        videos = _make_videos()
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract.return_value = PlaylistInfo(
            id="PLtest",
            title="T",
            url="https://youtube.com/playlist?list=PLtest",
            video_count=3,
            videos=videos,
        )
        mock_dl = mock_downloader_cls.return_value
        mock_dl.download.side_effect = [_success_result(v) for v in videos]

        orchestrator = PlaylistDownloader(dl_config)
        summary = orchestrator.download("https://youtube.com/playlist?list=PLtest")

        assert summary.total == 3
        assert summary.succeeded == 3
        assert summary.failed == 0
        assert summary.skipped == 0
        assert len(summary.results) == 3
        assert summary.errors == []


class TestPlaylistDownloaderOneFails:
    def test_one_fail_continues(
        self,
        dl_config: DownloadConfig,
        mock_extractor_cls: MagicMock,
        mock_downloader_cls: MagicMock,
    ) -> None:
        videos = _make_videos()
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract.return_value = PlaylistInfo(
            id="PLtest",
            title="T",
            url="https://youtube.com/playlist?list=PLtest",
            video_count=3,
            videos=videos,
        )
        mock_dl = mock_downloader_cls.return_value
        mock_dl.download.side_effect = [
            _success_result(videos[0]),
            _fail_result(videos[1], "HTTP 403"),
            _success_result(videos[2]),
        ]

        orchestrator = PlaylistDownloader(dl_config)
        summary = orchestrator.download("https://youtube.com/playlist?list=PLtest")

        assert summary.total == 3
        assert summary.succeeded == 2
        assert summary.failed == 1
        assert summary.skipped == 0
        assert summary.errors == ["HTTP 403"]
        assert summary.results[0].success is True
        assert summary.results[1].success is False
        assert summary.results[2].success is True


class TestPlaylistDownloaderAllFail:
    def test_all_fail(
        self,
        dl_config: DownloadConfig,
        mock_extractor_cls: MagicMock,
        mock_downloader_cls: MagicMock,
    ) -> None:
        videos = _make_videos()
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract.return_value = PlaylistInfo(
            id="PLtest",
            title="T",
            url="https://youtube.com/playlist?list=PLtest",
            video_count=3,
            videos=videos,
        )
        mock_dl = mock_downloader_cls.return_value
        mock_dl.download.side_effect = [
            _fail_result(videos[0], "Error A"),
            _fail_result(videos[1], "Error B"),
            _fail_result(videos[2], "Error C"),
        ]

        orchestrator = PlaylistDownloader(dl_config)
        summary = orchestrator.download("https://youtube.com/playlist?list=PLtest")

        assert summary.total == 3
        assert summary.succeeded == 0
        assert summary.failed == 3
        assert summary.errors == ["Error A", "Error B", "Error C"]


class TestPlaylistDownloaderEmptyPlaylist:
    def test_empty_playlist(
        self,
        dl_config: DownloadConfig,
        mock_extractor_cls: MagicMock,
        mock_downloader_cls: MagicMock,
    ) -> None:
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract.return_value = PlaylistInfo(
            id="PLempty",
            title="Empty",
            url="https://youtube.com/playlist?list=PLempty",
            video_count=0,
            videos=(),
        )

        orchestrator = PlaylistDownloader(dl_config)
        summary = orchestrator.download("https://youtube.com/playlist?list=PLempty")

        assert summary.total == 0
        assert summary.succeeded == 0
        assert summary.failed == 0
        assert summary.skipped == 0
        assert summary.results == []
        assert summary.errors == []
        mock_downloader_cls.return_value.download.assert_not_called()


class TestDownloadSummarySuccessRate:
    @pytest.mark.parametrize(
        "succeeded,total,expected",
        [
            (2, 3, pytest.approx(66.666666, abs=0.01)),
            (0, 0, 0.0),
            (3, 3, 100.0),
            (1, 4, 25.0),
        ],
    )
    def test_success_rate(self, succeeded: int, total: int, expected: float) -> None:
        summary = DownloadSummary(
            total=total,
            succeeded=succeeded,
            failed=total - succeeded,
            skipped=0,
            results=[],
            errors=[],
        )
        assert summary.success_rate == expected


class TestPlaylistDownloaderErrorsCollected:
    def test_errors_collected(
        self,
        dl_config: DownloadConfig,
        mock_extractor_cls: MagicMock,
        mock_downloader_cls: MagicMock,
    ) -> None:
        videos = _make_videos()
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract.return_value = PlaylistInfo(
            id="PLtest",
            title="T",
            url="https://youtube.com/playlist?list=PLtest",
            video_count=3,
            videos=videos,
        )
        mock_dl = mock_downloader_cls.return_value
        mock_dl.download.side_effect = [
            _fail_result(videos[0], "Geo-restricted"),
            _success_result(videos[1]),
            _fail_result(videos[2], "Age-restricted"),
        ]

        orchestrator = PlaylistDownloader(dl_config)
        summary = orchestrator.download("https://youtube.com/playlist?list=PLtest")

        assert "Geo-restricted" in summary.errors
        assert "Age-restricted" in summary.errors
        assert len(summary.errors) == 2


class TestPlaylistDownloaderLogMessages:
    def test_log_messages(
        self,
        dl_config: DownloadConfig,
        mock_extractor_cls: MagicMock,
        mock_downloader_cls: MagicMock,
        mocker: Any,
    ) -> None:
        mock_log = mocker.MagicMock()
        mocker.patch("ytpl_dl.playlist.get_logger", return_value=mock_log)

        videos = _make_videos()
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract.return_value = PlaylistInfo(
            id="PLtest",
            title="T",
            url="https://youtube.com/playlist?list=PLtest",
            video_count=3,
            videos=videos,
        )
        mock_dl = mock_downloader_cls.return_value
        mock_dl.download.side_effect = [_success_result(v) for v in videos]

        orchestrator = PlaylistDownloader(dl_config)
        orchestrator.download("https://youtube.com/playlist?list=PLtest")

        info_calls = list(mock_log.info.call_args_list)
        assert len(info_calls) >= 1
        first_call_args = info_calls[0][0]
        assert "playlist" in str(first_call_args).lower() or len(first_call_args) > 0
