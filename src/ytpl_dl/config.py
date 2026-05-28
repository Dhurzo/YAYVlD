from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ytpl_dl.errors import ConfigValidationError


@dataclass(frozen=True, slots=True)
class DownloadConfig:
    output_dir: Path = field(default_factory=lambda: Path("downloads"))
    format: str = "bestvideo+bestaudio/best"
    merge_output_format: str = "mkv"
    concurrent_fragments: int = 8
    retries: int = 10
    fragment_retries: int = 10
    timeout: int = 30
    download_archive: Path | None = None
    overwrite: bool = False
    proxy: str | None = None
    verbose: bool = False

    def __post_init__(self) -> None:
        if self.concurrent_fragments < 1 or self.concurrent_fragments > 16:
            raise ConfigValidationError(
                f"concurrent_fragments must be 1-16, got {self.concurrent_fragments}"
            )
        if self.retries < 0:
            raise ConfigValidationError(f"retries must be >= 0, got {self.retries}")
        if self.fragment_retries < 0:
            raise ConfigValidationError(
                f"fragment_retries must be >= 0, got {self.fragment_retries}"
            )
        if self.timeout < 1:
            raise ConfigValidationError(f"timeout must be >= 1, got {self.timeout}")

    @property
    def archive_path(self) -> Path | None:
        return self.download_archive
