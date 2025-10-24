"""Custom exceptions used throughout the conversion package."""

from __future__ import annotations


class ConversionError(RuntimeError):
    """Raised when a parser cannot convert a document."""


class UnsupportedFormatError(ValueError):
    """Raised when no plugin supports the requested file."""


class PluginRegistrationError(RuntimeError):
    """Raised when plugin registration fails."""
