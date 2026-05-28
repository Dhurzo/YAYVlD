from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VideoInfo:
    id: str
    title: str
    url: str
    duration: int | None = None
    index: int | None = None


@dataclass(frozen=True, slots=True)
class PlaylistInfo:
    id: str
    title: str
    url: str
    video_count: int
    videos: tuple[VideoInfo, ...]


@dataclass(frozen=True, slots=True)
class DownloadResult:
    video: VideoInfo
    success: bool
    file_path: Path | None = None
    error: str | None = None


def _format_bytes_value(num_bytes: float) -> str:
    if num_bytes < 0:
        num_bytes = 0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


@dataclass(frozen=True, slots=True)
class ProgressState:
    downloaded_bytes: int
    total_bytes: int | None
    speed: float | None = None
    eta: float | None = None
    filename: str = ""

    @property
    def percent(self) -> float:
        if self.total_bytes is None or self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100.0

    @property
    def speed_human(self) -> str:
        if self.speed is None:
            return "--- B/s"
        return f"{_format_bytes_value(self.speed)}/s"

    @property
    def eta_human(self) -> str:
        if self.eta is None:
            return "---"
        total_seconds = int(self.eta)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts: list[str] = []
        if hours > 0:
            parts.append(f"{hours}h")
        if hours > 0 or minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    @property
    def downloaded_human(self) -> str:
        return _format_bytes_value(float(self.downloaded_bytes))

    @property
    def total_human(self) -> str:
        if self.total_bytes is None:
            return "---"
        return _format_bytes_value(float(self.total_bytes))
