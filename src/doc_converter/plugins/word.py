from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..pandoc_runner import PandocRunConfig
from ..core import DocumentPlugin


class WordPlugin(DocumentPlugin):
    extensions = (".docx", ".doc")
    mime_types = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    )
    priority = 10

    def __init__(self) -> None:
        super().__init__()
        self._converted: list[Path] = []

    def prepare(self, path: Path, temp_dir: Path) -> PandocRunConfig:
        if path.suffix.lower() == ".docx":
            return PandocRunConfig(source_path=path, format_hint="docx")
        converted = self._convert_doc_to_docx(path, temp_dir)
        self._converted.append(converted)
        return PandocRunConfig(source_path=converted, format_hint="docx")

    def cleanup(self) -> None:
        for path in self._converted:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        self._converted.clear()

    def _convert_doc_to_docx(self, path: Path, temp_dir: Path) -> Path:
        soffice = shutil.which("libreoffice") or shutil.which("soffice")
        if not soffice:
            raise RuntimeError("LibreOffice/soffice executable not found in PATH")
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "docx",
                str(path),
                "--outdir",
                str(temp_dir),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        converted = temp_dir / (path.stem + ".docx")
        if not converted.exists():
            raise FileNotFoundError(converted)
        return converted
