from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlparse

import yt_dlp

from ytpl_dl.config import DownloadConfig
from ytpl_dl.downloader import VideoDownloader
from ytpl_dl.errors import PlaylistNotFoundError
from ytpl_dl.logging import get_logger
from ytpl_dl.models import DownloadResult, PlaylistInfo, VideoInfo

_VALID_DOMAINS = frozenset({"youtube.com", "www.youtube.com", "youtu.be", "www.youtu.be"})


class PlaylistExtractor:
    """Extract playlist metadata by wrapping ``yt_dlp.YoutubeDL``."""

    def __init__(self, config: DownloadConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, playlist_url: str) -> PlaylistInfo:
        """Return rich playlist metadata without downloading any video content."""
        self._validate_url(playlist_url)

        opts = self._build_ydl_opts()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(playlist_url, download=False)
        except yt_dlp.utils.ExtractorError as exc:
            raise PlaylistNotFoundError(f"Failed to extract playlist: {exc}") from exc

        if data is None:
            raise PlaylistNotFoundError(f"No data returned for URL: {playlist_url}")

        entries = data.get("entries") or []
        videos = tuple(self._parse_entry(entry, i + 1) for i, entry in enumerate(entries))

        return PlaylistInfo(
            id=data.get("id", ""),
            title=data.get("title", ""),
            url=playlist_url,
            video_count=len(videos),
            videos=videos,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_ydl_opts(self) -> dict[str, Any]:
        return {
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
        }

    def _parse_entry(self, entry: dict[str, Any], index: int) -> VideoInfo:
        duration = entry.get("duration")
        return VideoInfo(
            id=entry["id"],
            title=entry.get("title", ""),
            url=entry.get("url") or f"https://www.youtube.com/watch?v={entry['id']}",
            duration=int(duration) if duration is not None else None,
            index=index,
        )

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise PlaylistNotFoundError(f"Invalid playlist URL: {url}")

        if parsed.netloc not in _VALID_DOMAINS:
            raise PlaylistNotFoundError(f"Invalid playlist URL: {url}")

        # youtu.be short-links are accepted as potential playlist URLs
        if parsed.netloc in ("youtu.be", "www.youtu.be"):
            if not parsed.path.strip("/"):
                raise PlaylistNotFoundError(f"Invalid playlist URL: {url}")
            return

        path = parsed.path

        if path.startswith("/playlist"):
            params = parse_qs(parsed.query)
            if "list" not in params:
                raise PlaylistNotFoundError(
                    f"YouTube playlist URL must include a 'list' parameter: {url}"
                )
            return

        if path.startswith("/watch"):
            params = parse_qs(parsed.query)
            if "list" not in params:
                raise PlaylistNotFoundError(
                    f"YouTube watch URL must include a 'list' parameter to be treated as a playlist: {url}"
                )
            return

        raise PlaylistNotFoundError(f"Invalid playlist URL: {url}")


@dataclass(frozen=True, slots=True)
class DownloadSummary:
    total: int
    succeeded: int
    failed: int
    skipped: int
    results: list[DownloadResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.succeeded / self.total) * 100.0


class PlaylistDownloader:
    def __init__(self, config: DownloadConfig) -> None:
        self._config = config
        self._log = get_logger("playlist")

    def download(self, playlist_url: str) -> DownloadSummary:
        extractor = PlaylistExtractor(self._config)
        playlist = extractor.extract(playlist_url)

        self._log.info(
            "playlist_download_start",
            title=playlist.title,
            video_count=playlist.video_count,
        )

        downloader = VideoDownloader(self._config)
        results: list[DownloadResult] = []
        errors: list[str] = []
        succeeded = 0
        failed = 0

        for i, video in enumerate(playlist.videos, start=1):
            result = self._download_video(video, downloader, i, playlist.video_count)
            results.append(result)
            if result.success:
                succeeded += 1
            else:
                failed += 1
                if result.error is not None:
                    errors.append(result.error)

        summary = DownloadSummary(
            total=playlist.video_count,
            succeeded=succeeded,
            failed=failed,
            skipped=0,
            results=results,
            errors=errors,
        )

        self._log.info(
            "playlist_download_complete",
            total=summary.total,
            succeeded=summary.succeeded,
            failed=summary.failed,
            success_rate=summary.success_rate,
        )

        return summary

    def _download_video(
        self,
        video: VideoInfo,
        downloader: VideoDownloader,
        index: int,
        total: int,
    ) -> DownloadResult:
        self._log.info(
            "video_download_start",
            video_id=video.id,
            title=video.title,
            index=index,
            total=total,
        )
        result = downloader.download(video)
        self._log.info(
            "video_download_complete",
            video_id=video.id,
            success=result.success,
            index=index,
            total=total,
        )
        return result
