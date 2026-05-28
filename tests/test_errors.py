"""Tests for the exception hierarchy in ytpl_dl.errors."""

from __future__ import annotations

import pytest

from ytpl_dl.errors import (
    AgeRestrictedError,
    ConfigValidationError,
    DownloadFailedError,
    GeoRestrictedError,
    PlaylistNotFoundError,
    VideoUnavailableError,
    YtplDlError,
)

ALL_EXCEPTIONS = [
    YtplDlError,
    PlaylistNotFoundError,
    VideoUnavailableError,
    GeoRestrictedError,
    AgeRestrictedError,
    DownloadFailedError,
    ConfigValidationError,
]


class TestExceptionInstantiation:
    """Each exception must be instantiable with a message string."""

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_instantiable_with_message(self, exc_cls: type[YtplDlError]) -> None:
        exc = exc_cls("something went wrong")
        assert str(exc) == "something went wrong"

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_instantiable_with_empty_message(self, exc_cls: type[YtplDlError]) -> None:
        exc = exc_cls("")
        assert str(exc) == ""


class TestExceptionInheritance:
    """Each exception inherits from YtplDlError and Exception."""

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_inherits_ytpl_dl_error(self, exc_cls: type[YtplDlError]) -> None:
        assert issubclass(exc_cls, YtplDlError)

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_inherits_exception(self, exc_cls: type[YtplDlError]) -> None:
        assert issubclass(exc_cls, Exception)

    def test_ytpl_dl_error_is_base(self) -> None:
        """YtplDlError itself inherits from Exception."""
        assert issubclass(YtplDlError, Exception)


class TestExceptionCatching:
    """All specific exceptions are catchable via YtplDlError."""

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS[1:])  # skip base
    def test_catchable_as_ytpl_dl_error(self, exc_cls: type[YtplDlError]) -> None:
        with pytest.raises(YtplDlError, match="test message"):
            raise exc_cls("test message")

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_catchable_as_exception(self, exc_cls: type[YtplDlError]) -> None:
        with pytest.raises(Exception, match="boom"):
            raise exc_cls("boom")


class TestStrRepresentation:
    """str(error) returns the constructor message."""

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_str_returns_message(self, exc_cls: type[YtplDlError]) -> None:
        msg = "playlist PLxxxxx not found"
        exc = exc_cls(msg)
        assert str(exc) == msg
