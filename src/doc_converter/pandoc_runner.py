from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(slots=True)
class PandocRunConfig:
    source_path: Path
    format_hint: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class PandocRunner:
    """Runs pandoc and returns JSON AST structures."""

    def __init__(self, pandoc_path: Optional[str] = None):
        self._pandoc = pandoc_path or shutil.which("pandoc")
        if not self._pandoc:
            raise RuntimeError("pandoc executable not found in PATH")

    def run(self, config: PandocRunConfig) -> Dict:
        cmd = [self._pandoc]
        if config.format_hint:
            cmd.extend(["--from", config.format_hint])
        cmd.extend(["--to", "json", str(config.source_path)])
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
        )
        return json.loads(completed.stdout)
