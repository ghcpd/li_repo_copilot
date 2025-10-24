from __future__ import annotations

import json
import mimetypes
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, Optional

from .pandoc_runner import PandocRunner, PandocRunConfig
from .schema import DocumentSchemaBuilder


@dataclass(slots=True)
class ConversionResult:
    source: Path
    output: dict

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.output, indent=indent, ensure_ascii=False)


class DocumentPlugin(ABC):
    """Base class for document format plugins."""

    #: File extensions handled by this plugin. Include leading dot.
    extensions: tuple[str, ...] = ()
    #: Optional MIME types handled by the plugin.
    mime_types: tuple[str, ...] = ()
    #: Priority. Lower wins when multiple plugins match.
    priority: int = 100

    def matches(self, path: Path) -> bool:
        ext = path.suffix.lower()
        if ext in self.extensions:
            return True
        mime, _ = mimetypes.guess_type(path.name)
        return mime in self.mime_types

    @abstractmethod
    def prepare(self, path: Path, temp_dir: Path) -> PandocRunConfig:
        """Prepare the file and return pandoc configuration."""

    def cleanup(self) -> None:
        """Allow plugins to clean up transient resources."""


class DocumentConverter:
    """High-level coordinator that orchestrates plugins and Pandoc."""

    def __init__(self, plugins: Optional[Iterable[DocumentPlugin]] = None):
        self._plugins: List[DocumentPlugin] = sorted(
            plugins if plugins is not None else list(default_plugins()),
            key=lambda p: p.priority,
        )
        self._runner = PandocRunner()
        self._schema_builder = DocumentSchemaBuilder()

    def register_plugin(self, plugin: DocumentPlugin) -> None:
        self._plugins.append(plugin)
        self._plugins.sort(key=lambda p: p.priority)

    def available_plugins(self) -> tuple[DocumentPlugin, ...]:
        return tuple(self._plugins)

    def convert_file(self, path: Path) -> ConversionResult:
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(path)

        plugin = self._select_plugin(path)
        if plugin is None:
            raise ValueError(f"No plugin registered to handle {path.suffix or path}")

        with tempfile.TemporaryDirectory(prefix="doc-converter-") as tmp:
            tmp_dir = Path(tmp)
            config = plugin.prepare(path, tmp_dir)
            pandoc_json = self._runner.run(config)
            result = self._schema_builder.build(
                pandoc_json,
                source_path=config.source_path,
                declared_format=config.format_hint,
                original_path=path,
            )
        plugin.cleanup()
        return ConversionResult(source=path, output=result)

    def convert_path(self, path: Path, *, recursive: bool = True) -> Iterator[ConversionResult]:
        path = path.resolve()
        if path.is_file():
            yield self.convert_file(path)
            return

        if not path.is_dir():
            raise NotADirectoryError(path)

        walker: Callable[[Path], Iterator[Path]]
        if recursive:
            walker = lambda root: (p for p in root.rglob("*") if p.is_file())
        else:
            walker = lambda root: (p for p in root.iterdir() if p.is_file())

        for file_path in walker(path):
            try:
                yield self.convert_file(file_path)
            except ValueError:
                continue

    def _select_plugin(self, path: Path) -> Optional[DocumentPlugin]:
        matches: List[DocumentPlugin] = [p for p in self._plugins if p.matches(path)]
        if matches:
            return matches[0]
        return None


def default_plugins() -> Iterable[DocumentPlugin]:
    from .plugins.html import HTMLPlugin
    from .plugins.text import PlainTextPlugin
    from .plugins.word import WordPlugin

    yield WordPlugin()
    yield HTMLPlugin()
    yield PlainTextPlugin()
