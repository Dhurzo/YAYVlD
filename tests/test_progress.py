"""Tests for progress hook and formatting in ytpl_dl.progress."""

from __future__ import annotations

from unittest.mock import MagicMock

from ytpl_dl.models import ProgressState
from ytpl_dl.progress import create_progress_hook, format_bytes, format_progress


class TestCreateProgressHook:
    def test_returns_callable(self) -> None:
        hook = create_progress_hook()
        assert callable(hook)

    def test_downloading_calls_callback(self) -> None:
        callback = MagicMock()
        hook = create_progress_hook(callback)

        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 500,
                "total_bytes": 1000,
                "total_bytes_estimate": None,
                "speed": 1024.0,
                "eta": 10.0,
                "filename": "video.mkv",
            }
        )

        callback.assert_called_once()
        state = callback.call_args[0][0]
        assert isinstance(state, ProgressState)
        assert state.downloaded_bytes == 500
        assert state.total_bytes == 1000
        assert state.speed == 1024.0
        assert state.eta == 10.0
        assert state.filename == "video.mkv"

    def test_downloading_uses_estimate_when_total_none(self) -> None:
        callback = MagicMock()
        hook = create_progress_hook(callback)

        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 500,
                "total_bytes": None,
                "total_bytes_estimate": 2000,
                "speed": 512.0,
                "eta": 5.0,
                "filename": "video.mkv",
            }
        )

        state = callback.call_args[0][0]
        assert state.total_bytes == 2000

    def test_finished_does_not_call_callback(self) -> None:
        callback = MagicMock()
        hook = create_progress_hook(callback)

        hook(
            {
                "status": "finished",
                "downloaded_bytes": 1000,
                "total_bytes": 1000,
                "filename": "video.mkv",
            }
        )

        callback.assert_not_called()

    def test_error_does_not_crash(self) -> None:
        callback = MagicMock()
        hook = create_progress_hook(callback)

        hook(
            {
                "status": "error",
                "downloaded_bytes": 500,
                "total_bytes": 1000,
                "filename": "video.mkv",
            }
        )

        callback.assert_not_called()

    def test_no_callback_does_not_crash(self) -> None:
        hook = create_progress_hook()

        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 500,
                "total_bytes": 1000,
                "speed": 1024.0,
                "eta": 10.0,
                "filename": "video.mkv",
            }
        )


class TestFormatProgress:
    def test_with_title(self) -> None:
        state = ProgressState(
            downloaded_bytes=452000000,
            total_bytes=1000000000,
            speed=4200000.0,
            eta=150.0,
            filename="video.mkv",
        )
        result = format_progress(state, video_title="Cool Video")
        assert "45.2%" in result
        assert "Cool Video" in result

    def test_without_title(self) -> None:
        state = ProgressState(
            downloaded_bytes=500,
            total_bytes=1000,
            speed=1024.0,
            eta=30.0,
            filename="video.mkv",
        )
        result = format_progress(state)
        assert "50.0%" in result


class TestFormatBytes:
    def test_zero(self) -> None:
        assert format_bytes(0) == "0 B"

    def test_bytes(self) -> None:
        assert format_bytes(500) == "500.0 B"

    def test_kilobytes(self) -> None:
        assert format_bytes(1024) == "1.0 KB"

    def test_megabytes(self) -> None:
        assert format_bytes(1048576) == "1.0 MB"

    def test_gigabytes(self) -> None:
        assert format_bytes(1073741824) == "1.0 GB"

    def test_terabytes(self) -> None:
        assert format_bytes(1099511627776) == "1.0 TB"

    def test_partial_kilobytes(self) -> None:
        assert format_bytes(1536) == "1.5 KB"
