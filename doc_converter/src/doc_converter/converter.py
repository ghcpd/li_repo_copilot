"""High level conversion orchestrator."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator

from .exceptions import ConversionError
from .models import DocumentCollection, DocumentModel
from .plugins.base import FormatPlugin
from .registry import PluginRegistry, default_registry


class DocumentConverter:
    """Convert documents into the unified JSON representation using plugins."""

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self.registry = registry or default_registry()

    def convert_file(self, path: Path) -> DocumentModel:
        plugin = self.registry.detect(path)
        try:
            return plugin.parse(path)
        except Exception as exc:  # noqa: BLE001 - we re-wrap for callers
            raise ConversionError(f"Failed to parse '{path}': {exc}") from exc

    def convert_many(self, paths: Iterable[Path]) -> DocumentCollection:
        grouped: dict[FormatPlugin, list[Path]] = defaultdict(list)
        resolved_paths: list[Path] = []
        for path in paths:
            path = Path(path)
            resolved_paths.append(path)
            plugin = self.registry.detect(path)
            grouped[plugin].append(path)

        self.registry.batch_preload(grouped)
        documents_with_paths: list[tuple[DocumentModel, Path]] = []
        for plugin, files in grouped.items():
            for file_path in files:
                document = plugin.parse(file_path)
                documents_with_paths.append((document, file_path))

        documents_with_paths.sort(key=lambda item: resolved_paths.index(item[1]))
        documents = [doc for doc, _ in documents_with_paths]
        return DocumentCollection(documents)

    def convert_path(self, input_path: Path) -> DocumentCollection:
        input_path = Path(input_path)
        if input_path.is_file():
            return DocumentCollection([self.convert_file(input_path)])

        if input_path.is_dir():
            files = self._iter_supported_files(input_path)
            return self.convert_many(files)

        raise FileNotFoundError(f"Input path '{input_path}' does not exist")

    def _iter_supported_files(self, directory: Path) -> Iterator[Path]:
        for candidate in sorted(directory.rglob("*")):
            if candidate.is_file():
                try:
                    self.registry.detect(candidate)
                except Exception:
                    continue
                else:
                    yield candidate

    def write_json(self, documents: DocumentCollection, output_dir: Path, indent: int = 2) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        for document in documents.root:
            input_path = Path(document.metadata.source_path)
            output_path = output_dir / f"{input_path.stem}.json"
            output_path.write_text(json.dumps(document.as_json_dict(), indent=indent, ensure_ascii=False), "utf-8")


__all__ = ["DocumentConverter"]
