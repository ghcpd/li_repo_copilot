"""Plugin for legacy Microsoft Word DOC documents."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pypandoc

from ..exceptions import ConversionError
from ..models import DocumentMetadata, DocumentModel
from ..plugins.base import FormatPlugin
from .html_parser import HtmlProcessor


class DocPlugin(FormatPlugin):
    name = "doc"
    extensions = ("doc",)
    media_types = ("application/msword",)
    signatures = (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)

    def __init__(self, inline_images: bool = True) -> None:
        self.processor = HtmlProcessor(inline_images=inline_images)

    def parse(self, path: Path) -> DocumentModel:
        with tempfile.TemporaryDirectory() as extracted_media:
            try:
                html = pypandoc.convert_file(
                    str(path),
                    to="html",
                    format="doc",
                    extra_args=["--extract-media", extracted_media],
                )
            except RuntimeError as exc:  # pragma: no cover - pypandoc error paths
                raise ConversionError(f"Unable to convert '{path}' via pandoc: {exc}") from exc

            metadata = self._default_metadata(path)
            return self.processor.parse_html(
                html,
                source_path=str(path),
                metadata=metadata,
                base_path=Path(extracted_media),
            )

    @staticmethod
    def _default_metadata(path: Path) -> DocumentMetadata:
        return DocumentMetadata(
            title=path.stem,
            author=None,
            created_at=None,
            modified_at=None,
            subject=None,
            keywords=[],
            language=None,
            source_path=str(path),
        )


PLUGINS = [DocPlugin()]

