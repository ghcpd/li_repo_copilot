from __future__ import annotations

from pathlib import Path

from ..pandoc_runner import PandocRunConfig
from ..core import DocumentPlugin


class PlainTextPlugin(DocumentPlugin):
    extensions = (".txt",)
    mime_types = ("text/plain",)
    priority = 30

    def prepare(self, path: Path, temp_dir: Path) -> PandocRunConfig:
        return PandocRunConfig(source_path=path, format_hint="plain")
