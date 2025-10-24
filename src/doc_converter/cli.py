from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from .core import DocumentConverter


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert documents into unified JSON")
    parser.add_argument("path", type=Path, help="File or directory to convert")
    parser.add_argument("-o", "--output", type=Path, help="Directory to write JSON files")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recurse into sub-directories")
    parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout instead of writing files")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    converter = DocumentConverter()
    results = converter.convert_path(args.path, recursive=args.recursive)

    if args.stdout:
        for result in results:
            print(result.to_json())
        return 0

    output_dir = args.output or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        output_path = output_dir / f"{result.source.stem}.json"
        output_path.write_text(result.to_json(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
