# Yes Another Youtube Video List Downloader

[![CI](https://github.com/Dhurzo/YAYVlD/actions/workflows/ci.yml/badge.svg)](https://github.com/Dhurzo/YAYVlD/actions/workflows/ci.yml)

YouTube playlist downloader with maximum quality support, resume capability, and comprehensive error handling.

**Built with GLM-4.7 using Spec-Driven Development (AI)** - This software was developed using GLM-4.7's advanced AI capabilities with a specification-driven development approach, ensuring high code quality, comprehensive test coverage, and adherence to modern Python best practices.

## Features

- ✅ **Maximum Quality**: Downloads best video + best audio, merged to MKV
- ✅ **Resume Support**: HTTP Range headers + download archive for interrupted downloads
- ✅ **Error Recovery**: Retry logic with exponential backoff (10 retries)
- ✅ **Progress Tracking**: Real-time percentage, speed, ETA
- ✅ **Exit Codes**: Proper exit codes for automation (0=success, 1=partial, 2=fatal)
- ✅ **Proxy Support**: HTTP/HTTPS proxy configuration
- ✅ **Production Logging**: Structured logging (console/JSON modes)
- ✅ **Modern Python 3.12+**: Strict type checking, comprehensive test coverage (94.26%)

## Installation

### Prerequisites

- Python 3.12 or later
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- FFmpeg (required for merging video+audio)

### Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### Install ytpl-dl

**Using uv (recommended):**
```bash
uv tool install ytpl-dl
```

**Using pip:**
```bash
pip install ytpl-dl
```

### Verify Installation

```bash
ytpl-dl download --help
```

## Quick Start

Download a playlist with default settings (max quality, 8 concurrent fragments, 10 retries):

```bash
ytpl-dl download "https://www.youtube.com/playlist?list=PLRKwNA8aMjGBcOOa4wTDZDV2ojgjcvBwX"
```

Videos are saved to `downloads/` directory as MKV files with naming:
```
downloads/
├── 001 - Video Title [video_id].mkv
├── 002 - Another Video [video_id2].mkv
└── .download_archive  # Tracks downloaded videos for resume
```

## Usage

### Basic Usage

```bash
# Download with default settings
ytpl-dl download "https://www.youtube.com/playlist?list=..."

# Specify output directory
ytpl-dl download "https://www.youtube.com/playlist?list=..." -o my_videos

# Enable verbose logging
ytpl-dl download "https://www.youtube.com/playlist?list=..." -v

# Disable resume (no archive file)
ytpl-dl download "https://www.youtube.com/playlist?list=..." --no-archive

# Overwrite existing files
ytpl-dl download "https://www.youtube.com/playlist?list=..." --overwrite
```

### Advanced Options

```bash
# Custom format selection
ytpl-dl download "https://www.youtube.com/playlist?list=..." -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"

# Adjust concurrent fragment downloads (1-16, default: 8)
ytpl-dl download "https://www.youtube.com/playlist?list=..." -c 4

# Change retry count
ytpl-dl download "https://www.youtube.com/playlist?list=..." -r 5

# Use proxy
ytpl-dl download "https://www.youtube.com/playlist?list=..." -p "http://127.0.0.1:8080"

# JSON structured logging
ytpl-dl download "https://www.youtube.com/playlist?list=..." --json-log
```

### Format Strings

Common format options:

- `"bestvideo+bestaudio/best"` - Best quality with merging (default)
- `"best"` - Best single file (no merging)
- `"bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"` - Prefer MP4 video + M4A audio
- `"1080"` - Download 1080p or best available
- `"worst"` - Lowest quality

## Exit Codes

| Code | Meaning | Automation Behavior |
|------|---------|---------------------|
| 0 | All videos downloaded successfully | Continue |
| 1 | Some videos failed (partial success) | Check summary, may retry |
| 2 | Fatal error (invalid URL, config, network) | Manual intervention required |

## Output

### Progress Display

```
Downloading "Video Title 1" — 45.2% | 4.2 MB/s | ETA 2m 30s
Downloading "Video Title 1" — 100% | Completed
Downloading "Video Title 2" — 12.8% | 3.1 MB/s | ETA 8m 15s
```

### Final Summary

```
Download Summary:
  Total: 50 videos
  Succeeded: 45 videos
  Failed: 5 videos
  Skipped: 0 videos
  Success rate: 90.0%

Errors:
  - Video Title 12: HTTP Error 403: Forbidden
  - Video Title 23: GeoRestricted: This video is not available in your country
  - Video Title 34: AgeRestricted: Sign in to confirm your age
  - Video Title 41: Unavailable: Private video
  - Video Title 47: DownloadFailed: Connection timeout
```

## Error Handling

ytpl-dl handles various error scenarios:

- **Network failures**: Retry with exponential backoff (up to 10 attempts)
- **Age-restricted videos**: Clear error message, continues to next video
- **Geo-restricted videos**: Clear error message, continues to next video
- **Private/deleted videos**: Clear error message, continues to next video
- **Invalid URLs**: Fatal error with exit code 2

## Resume Capability

The `.download_archive` file tracks successfully downloaded videos. If interrupted, rerun the same command to continue:

```bash
# First run (interrupted at video 25)
ytpl-dl download "https://www.youtube.com/playlist?list=..."

# Resume - skips first 24 videos, starts at 25
ytpl-dl download "https://www.youtube.com/playlist?list=..."
```

To disable resume (download everything fresh):

```bash
ytpl-dl download "https://www.youtube.com/playlist?list=..." --no-archive --overwrite
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/ytpl-dl.git
cd ytpl-dl

# Install development dependencies
uv sync

# Run tests
uv run pytest

# Type checking
uv run mypy src/ --strict

# Lint
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Run Tests with Coverage

```bash
uv run pytest --cov=ytpl_dl --cov-report=term-missing -v
```

### Project Structure

```
ytpl-dl/
├── pyproject.toml          # Project configuration
├── src/ytpl_dl/
│   ├── __init__.py        # Package init
│   ├── __main__.py        # Module entry point
│   ├── cli.py             # Typer CLI interface
│   ├── config.py          # DownloadConfig with validation
│   ├── downloader.py      # VideoDownloader (yt-dlp wrapper)
│   ├── errors.py          # Exception hierarchy
│   ├── logging.py         # Structured logging setup
│   ├── models.py          # Domain models (VideoInfo, PlaylistInfo, etc.)
│   ├── playlist.py        # PlaylistExtractor + PlaylistDownloader
│   └── progress.py        # Progress hooks and formatting
└── tests/
    ├── conftest.py        # Shared fixtures
    ├── test_cli.py        # CLI tests
    ├── test_config.py     # Config tests
    ├── test_downloader.py # VideoDownloader tests
    ├── test_errors.py     # Exception tests
    ├── test_models.py     # Model tests
    ├── test_playlist.py   # Playlist tests
    ├── test_progress.py   # Progress tests
    └── test_logging.py    # Logging tests
```

## Architecture

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **yt-dlp** | Active fork (166K★), handles age/geo restrictions, concurrent fragments |
| **Typer CLI** | Type-hint based, auto-completion, modern Python best practices |
| **Sequential playlist + concurrent fragments** | Battle-tested pattern, simpler error handling |
| **HTTP Range resume** | Production-proven pattern for interrupted downloads |
| **structlog** | Structured JSON for production, human-readable for console |
| **Frozen dataclasses** | Immutable models, hashable, type-safe |

### Components

- **CLI** (`cli.py`): Typer app with command-line argument parsing
- **Config** (`config.py`): Configuration with validation
- **PlaylistExtractor** (`playlist.py`): Extracts playlist metadata without downloading
- **VideoDownloader** (`downloader.py`): Wraps yt-dlp with error translation
- **PlaylistDownloader** (`playlist.py`): Orchestrates sequential downloads with error recovery
- **Models** (`models.py`): Domain types (VideoInfo, PlaylistInfo, DownloadResult, ProgressState)
- **Errors** (`errors.py`): Exception hierarchy for domain errors

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass (`uv run pytest`)
5. Ensure type checking passes (`uv run mypy src/ --strict`)
6. Ensure linting passes (`uv run ruff check src/ tests/`)
7. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube download library
- [Typer](https://github.com/tiangolo/typer) - CLI framework
- [structlog](https://github.com/hynek/structlog) - Structured logging

## Alternatives

- **yt-dlp CLI**: Direct yt-dlp usage (more options, less polished)
- **youtube-dl**: Deprecated, use yt-dlp instead
- **youtube-dlc**: Inactive, use yt-dlp instead

## Troubleshooting

### FFmpeg Not Found

```
Error: FFmpeg not found
```

Install FFmpeg and ensure it's in your PATH. See [Installation](#install-ffmpeg).

### Age-Restricted Videos

Some videos require age verification. Try:

```bash
# Use cookies from browser
yt-dlp --cookies-from-browser chrome URL
```

### Geo-Restricted Videos

Use a VPN or proxy:

```bash
ytpl-dl download "URL" -p "http://proxy:8080"
```

### Slow Downloads

Reduce concurrent fragment downloads to avoid throttling:

```bash
ytpl-dl download "URL" -c 2
```

## Changelog

### 0.1.0 (2025-05-28)

- Initial release
- Maximum quality downloads (bestvideo+bestaudio/best)
- Resume support with HTTP Range headers
- Error recovery with retry logic
- Progress tracking with percentage, speed, ETA
- Exit codes for automation
- Proxy support
- Structured logging
- 94.26% test coverage
- Full type checking with mypy strict
