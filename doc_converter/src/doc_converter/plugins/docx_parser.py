"""Plugin for Microsoft Word DOCX documents."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pypandoc
from docx import Document as DocxDocument

from ..exceptions import ConversionError
from ..models import DocumentMetadata, DocumentModel
from ..plugins.base import FormatPlugin
from .html_parser import HtmlProcessor


class DocxPlugin(FormatPlugin):
    name = "docx"
    extensions = ("docx",)
    media_types = ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",)
    signatures = (b"PK\x03\x04",)

    def __init__(self, inline_images: bool = True) -> None:
        self.processor = HtmlProcessor(inline_images=inline_images)

    def parse(self, path: Path) -> DocumentModel:
        metadata = self._extract_metadata(path)
        with tempfile.TemporaryDirectory() as extracted_media:
            extra_args = ["--extract-media", extracted_media]
            try:
                html = pypandoc.convert_file(str(path), to="html", format="docx", extra_args=extra_args)
            except RuntimeError as exc:  # pragma: no cover - pypandoc error paths
                raise ConversionError(f"Unable to convert '{path}' via pandoc: {exc}") from exc

            return self.processor.parse_html(
                html,
                source_path=str(path),
                metadata=metadata,
                base_path=Path(extracted_media),
            )

    def _extract_metadata(self, path: Path) -> DocumentMetadata:
        document = DocxDocument(str(path))
        props = document.core_properties
        keywords = self._split_keywords(props.keywords)
        return DocumentMetadata(
            title=props.title or path.stem,
            author=props.author or props.last_modified_by or None,
            created_at=self._safe_datetime(props.created),
            modified_at=self._safe_datetime(props.modified),
            subject=getattr(props, "subject", None) or None,
            keywords=keywords,
            language=getattr(props, "language", None) or None,
            source_path=str(path),
        )

    @staticmethod
    def _split_keywords(value: Optional[str]) -> list[str]:
        if not value:
            return []
        return [part.strip() for part in value.split(",") if part.strip()]

    @staticmethod
    def _safe_datetime(value: object) -> Optional[datetime]:
        return value if isinstance(value, datetime) else None


PLUGINS = [DocxPlugin()]

