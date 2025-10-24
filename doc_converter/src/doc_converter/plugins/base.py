"""Base plugin classes and utility helpers."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Iterable, Sequence

from ..models import DocumentModel

HEADER_SAMPLE_BYTES = 4096


class FormatPlugin(abc.ABC):
    """Abstract base class for document format plugins."""

    #: Unique name of the format handled by the plugin (e.g. ``"docx"``).
    name: str

    #: File extensions recognised by the plugin, without leading dot.
    extensions: Sequence[str] = ()

    #: Optional MIME types supported by the plugin.
    media_types: Sequence[str] = ()

    #: A tuple of header signatures that can be used to identify the file.
    signatures: Sequence[bytes] = ()

    def matches(self, path: Path, header: bytes) -> bool:
        """Return ``True`` if the plugin can parse *path*.

        The base implementation checks the file extension and header signatures.
        Plugins may override this method for more advanced heuristics.
        """

        suffix = path.suffix.lower().lstrip(".")
        if suffix and suffix in (ext.lower() for ext in self.extensions):
            return True

        if self.signatures and any(header.startswith(sig) for sig in self.signatures):
            return True

        return False

    @abc.abstractmethod
    def parse(self, path: Path) -> DocumentModel:
        """Parse *path* and return a :class:`DocumentModel`."""

    def batch_preload(self, paths: Iterable[Path]) -> None:
        """Allow plugins to perform batching pre-processing.

        Plugins that do not require any preloading can ignore this hook."""

        return None
