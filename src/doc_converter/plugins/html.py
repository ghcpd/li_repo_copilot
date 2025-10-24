from __future__ import annotations

from pathlib import Path

from ..pandoc_runner import PandocRunConfig
from ..core import DocumentPlugin


class HTMLPlugin(DocumentPlugin):
    extensions = (".html", ".htm")
    mime_types = ("text/html",)
    priority = 20

    def prepare(self, path: Path, temp_dir: Path) -> PandocRunConfig:
        return PandocRunConfig(source_path=path, format_hint="html")
