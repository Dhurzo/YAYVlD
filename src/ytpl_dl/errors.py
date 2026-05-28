"""Exception hierarchy for ytpl-dl."""

from __future__ import annotations


class YtplDlError(Exception):
    """Base exception for all ytpl-dl errors."""


class PlaylistNotFoundError(YtplDlError):
    """Playlist URL is invalid or playlist does not exist."""


class VideoUnavailableError(YtplDlError):
    """Video is unavailable (deleted, private)."""


class GeoRestrictedError(YtplDlError):
    """Video is blocked in the user's region."""


class AgeRestrictedError(YtplDlError):
    """Video requires age verification."""


class DownloadFailedError(YtplDlError):
    """Download failed after retries. Wraps yt-dlp DownloadError."""


class ConfigValidationError(YtplDlError):
    """Invalid configuration value."""
