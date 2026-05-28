from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ytpl_dl.models import ProgressState


def create_progress_hook(
    callback: Callable[[ProgressState], None] | None = None,
) -> Callable[[dict[str, Any]], None]:
    def hook(d: dict[str, Any]) -> None:
        if d.get("status") != "downloading":
            return
        if callback is None:
            return
        state = ProgressState(
            downloaded_bytes=d.get("downloaded_bytes", 0),
            total_bytes=d.get("total_bytes") or d.get("total_bytes_estimate"),
            speed=d.get("speed"),
            eta=d.get("eta"),
            filename=d.get("filename", ""),
        )
        callback(state)

    return hook


def format_progress(state: ProgressState, video_title: str | None = None) -> str:
    title_part = f'"{video_title}"' if video_title else state.filename
    return (
        f"Downloading {title_part} — "
        f"{state.percent:.1f}% | "
        f"{state.speed_human} | "
        f"ETA {state.eta_human}"
    )


def format_bytes(num_bytes: float) -> str:
    if num_bytes == 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
