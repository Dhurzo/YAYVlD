from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import (
    DownloadError,
    ExtractorError,
)
from yt_dlp.utils import (
    GeoRestrictedError as YtdlpGeoError,
)

from ytpl_dl.config import DownloadConfig
from ytpl_dl.errors import (
    AgeRestrictedError,
    DownloadFailedError,
    GeoRestrictedError,
    VideoUnavailableError,
    YtplDlError,
)
from ytpl_dl.models import DownloadResult, ProgressState, VideoInfo
from ytpl_dl.progress import create_progress_hook


class VideoDownloader:
    def __init__(
        self,
        config: DownloadConfig,
        progress_callback: Callable[[ProgressState], None] | None = None,
    ) -> None:
        self._config = config
        self._progress_callback = progress_callback

    def download(self, video: VideoInfo) -> DownloadResult:
        opts = self._build_ydl_opts(video)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video.url])
                filename = ydl.prepare_filename(
                    {
                        "title": video.title,
                        "id": video.id,
                        "ext": self._config.merge_output_format,
                    }
                )
                return DownloadResult(
                    video=video,
                    success=True,
                    file_path=Path(filename),
                )
        except Exception as e:
            domain_error = self._translate_error(e)
            return DownloadResult(
                video=video,
                success=False,
                error=str(domain_error),
            )

    def _build_ydl_opts(self, video: VideoInfo) -> dict[str, Any]:
        index_padded = f"{video.index:03d}" if video.index is not None else "000"

        opts: dict[str, Any] = {
            "format": self._config.format,
            "merge_output_format": self._config.merge_output_format,
            "outtmpl": str(
                self._config.output_dir / f"{index_padded} - %(title).200B [%(id)s].%(ext)s"
            ),
            "concurrent_fragment_downloads": self._config.concurrent_fragments,
            "retries": self._config.retries,
            "fragment_retries": self._config.fragment_retries,
            "retry_sleep_functions": {
                "http": lambda n: min(2**n, 60),
                "fragment": lambda n: 5,
            },
            "socket_timeout": self._config.timeout,
            "overwrites": self._config.overwrite,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [create_progress_hook(self._progress_callback)],
        }
        if self._config.archive_path is not None:
            opts["download_archive"] = str(self._config.archive_path)
        if self._config.proxy:
            opts["proxy"] = self._config.proxy
        return opts

    def _translate_error(self, error: Exception) -> YtplDlError:
        if isinstance(error, YtdlpGeoError):
            return GeoRestrictedError(str(error))
        if isinstance(error, ExtractorError):
            msg = str(error).lower()
            if "age" in msg or "sign in" in msg:
                return AgeRestrictedError(str(error))
            if "unavailable" in msg or "private" in msg or "deleted" in msg:
                return VideoUnavailableError(str(error))
            return DownloadFailedError(str(error))
        if isinstance(error, DownloadError):
            return DownloadFailedError(str(error))
        return DownloadFailedError(f"Unexpected error: {error}")
