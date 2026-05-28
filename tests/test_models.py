"""Tests for domain models in ytpl_dl.models."""

from __future__ import annotations

import pytest

from ytpl_dl.models import (
    DownloadResult,
    PlaylistInfo,
    ProgressState,
    VideoInfo,
)


class TestVideoInfo:
    def test_creation_with_required_fields(self) -> None:
        v = VideoInfo(id="abc123", title="Test Video", url="https://youtube.com/watch?v=abc123")
        assert v.id == "abc123"
        assert v.title == "Test Video"
        assert v.url == "https://youtube.com/watch?v=abc123"
        assert v.duration is None
        assert v.index is None

    def test_creation_with_all_fields(self) -> None:
        v = VideoInfo(
            id="abc123",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
            duration=300,
            index=5,
        )
        assert v.duration == 300
        assert v.index == 5

    def test_frozen_raises_on_assignment(self) -> None:
        v = VideoInfo(id="abc", title="t", url="u")
        with pytest.raises(AttributeError):
            v.title = "new"  # type: ignore[misc]

    def test_hashable(self) -> None:
        v = VideoInfo(id="abc", title="t", url="u")
        assert hash(v) == hash(v)
        s = {v}
        assert len(s) == 1


class TestPlaylistInfo:
    def _make_videos(self, count: int) -> tuple[VideoInfo, ...]:
        return tuple(
            VideoInfo(id=f"vid{i}", title=f"Video {i}", url=f"https://youtube.com/watch?v=vid{i}")
            for i in range(count)
        )

    def test_creation(self) -> None:
        videos = self._make_videos(3)
        pl = PlaylistInfo(
            id="PLxxx",
            title="My Playlist",
            url="https://youtube.com/playlist?list=PLxxx",
            video_count=3,
            videos=videos,
        )
        assert pl.id == "PLxxx"
        assert pl.title == "My Playlist"
        assert pl.video_count == 3
        assert len(pl.videos) == 3

    def test_frozen_raises_on_assignment(self) -> None:
        pl = PlaylistInfo(id="PLx", title="t", url="u", video_count=0, videos=())
        with pytest.raises(AttributeError):
            pl.title = "new"  # type: ignore[misc]

    def test_hashable(self) -> None:
        pl = PlaylistInfo(id="PLx", title="t", url="u", video_count=0, videos=())
        assert hash(pl) == hash(pl)


class TestDownloadResult:
    def _sample_video(self) -> VideoInfo:
        return VideoInfo(id="abc", title="Test", url="https://youtube.com/watch?v=abc")

    def test_success_case(self) -> None:
        from pathlib import Path

        v = self._sample_video()
        result = DownloadResult(
            video=v,
            success=True,
            file_path=Path("/tmp/video.mkv"),
        )
        assert result.success is True
        assert result.file_path == Path("/tmp/video.mkv")
        assert result.error is None

    def test_failure_case(self) -> None:
        v = self._sample_video()
        result = DownloadResult(
            video=v,
            success=False,
            error="Network timeout",
        )
        assert result.success is False
        assert result.error == "Network timeout"
        assert result.file_path is None

    def test_frozen(self) -> None:
        result = DownloadResult(video=self._sample_video(), success=True)
        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


class TestProgressState:
    def test_percent_with_known_total(self) -> None:
        state = ProgressState(downloaded_bytes=500, total_bytes=1000)
        assert state.percent == 50.0

    def test_percent_with_none_total(self) -> None:
        state = ProgressState(downloaded_bytes=500, total_bytes=None)
        assert state.percent == 0.0

    def test_percent_zero_total(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=0)
        assert state.percent == 0.0

    def test_speed_human_bytes(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, speed=500.0)
        assert state.speed_human == "500.0 B/s"

    def test_speed_human_kilobytes(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, speed=1024.0)
        assert state.speed_human == "1.0 KB/s"

    def test_speed_human_megabytes(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, speed=1024 * 1024 * 4.2)
        assert state.speed_human == "4.2 MB/s"

    def test_speed_human_gigabytes(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, speed=1024**3 * 1.5)
        assert state.speed_human == "1.5 GB/s"

    def test_speed_human_none(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, speed=None)
        assert state.speed_human == "--- B/s"

    def test_eta_human_seconds_only(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, eta=45.0)
        assert state.eta_human == "45s"

    def test_eta_human_minutes_and_seconds(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, eta=150.0)
        assert state.eta_human == "2m 30s"

    def test_eta_human_hours(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, eta=3661.0)
        assert state.eta_human == "1h 1m 1s"

    def test_eta_human_none(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None, eta=None)
        assert state.eta_human == "---"

    def test_downloaded_human(self) -> None:
        state = ProgressState(downloaded_bytes=1024 * 512, total_bytes=1024 * 1024)
        assert state.downloaded_human == "512.0 KB"

    def test_total_human(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=1024 * 1024 * 100)
        assert state.total_human == "100.0 MB"

    def test_total_human_none(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None)
        assert state.total_human == "---"

    def test_frozen(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=None)
        with pytest.raises(AttributeError):
            state.downloaded_bytes = 100  # type: ignore[misc]

    def test_hashable(self) -> None:
        state = ProgressState(downloaded_bytes=0, total_bytes=100)
        assert hash(state) == hash(state)
