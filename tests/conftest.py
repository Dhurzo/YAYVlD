from __future__ import annotations

from pathlib import Path

import pytest

from ytpl_dl.models import DownloadResult, PlaylistInfo, ProgressState, VideoInfo


@pytest.fixture
def sample_video() -> VideoInfo:
    return VideoInfo(
        id="dQw4w9WgXcQ",
        title="Rick Astley - Never Gonna Give You Up",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        duration=212,
        index=1,
    )


@pytest.fixture
def sample_videos() -> tuple[VideoInfo, ...]:
    return (
        VideoInfo(id="vid1", title="Video 1", url="https://youtube.com/watch?v=vid1", duration=120),
        VideoInfo(id="vid2", title="Video 2", url="https://youtube.com/watch?v=vid2", duration=300),
        VideoInfo(id="vid3", title="Video 3", url="https://youtube.com/watch?v=vid3", duration=180),
    )


@pytest.fixture
def sample_playlist(sample_videos: tuple[VideoInfo, ...]) -> PlaylistInfo:
    return PlaylistInfo(
        id="PLtest123",
        title="Test Playlist",
        url="https://www.youtube.com/playlist?list=PLtest123",
        video_count=len(sample_videos),
        videos=sample_videos,
    )


@pytest.fixture
def successful_download(sample_video: VideoInfo, tmp_path: Path) -> DownloadResult:
    return DownloadResult(
        video=sample_video,
        success=True,
        file_path=tmp_path / "Rick Astley - Never Gonna Give You Up.mkv",
    )


@pytest.fixture
def failed_download(sample_video: VideoInfo) -> DownloadResult:
    return DownloadResult(
        video=sample_video,
        success=False,
        error="HTTP Error 403: Forbidden",
    )


@pytest.fixture
def sample_progress() -> ProgressState:
    return ProgressState(
        downloaded_bytes=50_000_000,
        total_bytes=100_000_000,
        speed=4_200_000.0,
        eta=12.5,
        filename="video.mkv",
    )
