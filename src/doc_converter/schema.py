from __future__ import annotations

import itertools
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _to_iso(value: Optional[str] = None) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).isoformat()
    except ValueError:
        return None


class DocumentSchemaBuilder:
    """Transforms Pandoc AST into the unified JSON schema."""

    schema_version = "1.0.0"

    def build(
        self,
        pandoc_ast: Dict[str, Any],
        *,
        source_path: Path,
        declared_format: Optional[str],
        original_path: Path,
    ) -> Dict[str, Any]:
        meta = self._parse_meta(pandoc_ast.get("meta", {}), original_path)
        blocks = pandoc_ast.get("blocks", [])
        walker = BlockWalker()
        content = walker.walk(blocks)
        word_count = sum(segment.word_count for segment in walker.inline_segments)
        return {
            "schema_version": self.schema_version,
            "document": {
                "source": {
                    "path": str(original_path),
                    "format": declared_format or self._infer_format(original_path),
                    "size_bytes": original_path.stat().st_size,
                },
                "metadata": meta,
                "statistics": {
                    "word_count": word_count,
                    "block_counts": dict(Counter(item["type"] for item in content)),
                },
                "resources": walker.resources,
                "content": content,
            },
        }

    def _infer_format(self, path: Path) -> str:
        return path.suffix.lower().lstrip(".")

    def _parse_meta(self, meta: Dict[str, Any], path: Path) -> Dict[str, Any]:
        core: Dict[str, Any] = {
            "title": self._stringify_meta(meta.get("title")),
            "authors": self._string_list(meta.get("author")),
            "keywords": self._string_list(meta.get("keywords")),
            "published": _to_iso(self._stringify_meta(meta.get("date"))),
        }
        stat = path.stat()
        core.update(
            {
                "created_at": datetime.fromtimestamp(getattr(stat, "st_ctime", stat.st_mtime), tz=timezone.utc).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
        return core

    def _stringify_meta(self, node: Any) -> Optional[str]:
        if node is None:
            return None
        if isinstance(node, str):
            return node
        if isinstance(node, (list, tuple)):
            parts = [self._stringify_meta(part) for part in node]
            return "".join(filter(None, parts)) or None
        if isinstance(node, dict):
            if "t" in node and node["t"] == "MetaInlines":
                return self._stringify_meta(node.get("c"))
            if "t" in node and node["t"] == "MetaString":
                return node.get("c")
            if "c" in node:
                return self._stringify_meta(node["c"])
        return None

    def _string_list(self, node: Any) -> List[str]:
        if not node:
            return []
        if isinstance(node, list):
            return [value for value in (self._stringify_meta(item) for item in node) if value]
        value = self._stringify_meta(node)
        return [value] if value else []


class InlineSegment:
    """Represents a styled inline text segment."""

    __slots__ = ("text", "styles")

    def __init__(self, text: str, styles: Iterable[str]):
        self.text = text
        self.styles = tuple(styles)

    @property
    def word_count(self) -> int:
        return len(list(filter(None, self.text.split())))

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "styles": list(self.styles)}


class BlockWalker:
    """Walks Pandoc blocks and collects structured content."""

    def __init__(self) -> None:
        self.inline_segments: List[InlineSegment] = []
        self.resources: Dict[str, List[Dict[str, Any]]] = {
            "images": [],
            "links": [],
        }

    def walk(self, blocks: List[Any]) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []
        for index, block in enumerate(blocks):
            handler_name = f"_handle_{block['t'].lower()}"
            handler = getattr(self, handler_name, self._handle_generic)
            result = handler(index, block.get("c"))
            if result:
                if isinstance(result, list):
                    content.extend(result)
                else:
                    content.append(result)
        return content

    # Handler implementations -------------------------------------------------

    def _handle_header(self, index: int, payload: Any) -> Dict[str, Any]:
        (level, identifier, classes, kv_pairs), inlines = payload
        text_segments = self._flatten_inlines(inlines, block_index=index, block_type="heading")
        return {
            "id": identifier or f"heading-{index}",
            "type": "heading",
            "level": level,
            "position": {"block_index": index},
            "classes": classes,
            "attributes": dict(kv_pairs),
            "text_segments": text_segments,
            "text": "".join(segment["text"] for segment in text_segments),
        }

    def _handle_para(self, index: int, payload: Any) -> Dict[str, Any]:
        text_segments = self._flatten_inlines(payload, block_index=index, block_type="paragraph")
        return {
            "id": f"paragraph-{index}",
            "type": "paragraph",
            "position": {"block_index": index},
            "text_segments": text_segments,
            "text": "".join(segment["text"] for segment in text_segments),
        }

    def _handle_plain(self, index: int, payload: Any) -> Dict[str, Any]:
        return self._handle_para(index, payload)

    def _handle_bulletlist(self, index: int, payload: Any) -> Dict[str, Any]:
        items = [self._flatten_list_item(item, index, i, ordered=False) for i, item in enumerate(payload)]
        return {
            "id": f"list-{index}",
            "type": "list",
            "ordered": False,
            "position": {"block_index": index},
            "items": items,
        }

    def _handle_orderedlist(self, index: int, payload: Any) -> Dict[str, Any]:
        attrs, items = payload
        start = attrs[0]
        items_payload = [self._flatten_list_item(item, index, i, ordered=True) for i, item in enumerate(items, start=start)]
        return {
            "id": f"list-{index}",
            "type": "list",
            "ordered": True,
            "start": start,
            "position": {"block_index": index},
            "items": items_payload,
        }

    def _handle_table(self, index: int, payload: Any) -> Dict[str, Any]:
        attrs, caption, col_specs, head, bodies, foot = payload
        table = {
            "id": attrs[0] or f"table-{index}",
            "type": "table",
            "position": {"block_index": index},
            "caption": self._flatten_inlines(caption[1], block_index=index, block_type="table-caption") if caption else [],
            "columns": [spec[0] for spec in col_specs],
            "header": [self._flatten_inlines(cell[0][0], block_index=index, block_type="table-header") for cell in head[1]],
            "rows": [],
        }
        for body in bodies:
            for row in body[2]:
                row_cells = []
                for cell in row[1]:
                    row_cells.append(
                        self._flatten_inlines(cell[0], block_index=index, block_type="table-cell")
                    )
                table["rows"].append(row_cells)
        return table

    def _handle_codeblock(self, index: int, payload: Any) -> Dict[str, Any]:
        attrs, text = payload
        segment = InlineSegment(text, ["code"]).to_dict()
        self.inline_segments.append(InlineSegment(text, ["code"]))
        return {
            "id": attrs[0] or f"code-{index}",
            "type": "code",
            "language": attrs[1][0] if attrs[1] else None,
            "position": {"block_index": index},
            "text_segments": [segment],
            "text": text,
        }

    def _handle_blockquote(self, index: int, payload: Any) -> Dict[str, Any]:
        walker = BlockWalker()
        nested = walker.walk(payload)
        self.inline_segments.extend(walker.inline_segments)
        for key, value in walker.resources.items():
            self.resources[key].extend(value)
        return {
            "id": f"blockquote-{index}",
            "type": "blockquote",
            "position": {"block_index": index},
            "children": nested,
        }

    def _handle_generic(self, index: int, payload: Any):
        return None

    # Supporting helpers ------------------------------------------------------

    def _flatten_inlines(
        self,
        inlines: List[Any],
        *,
        block_index: int,
        block_type: str,
        styles: Optional[List[str]] = None,
        link_target: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        segments: List[Dict[str, Any]] = []
        styles = list(styles or [])
        for inline in inlines:
            kind = inline["t"]
            content = inline.get("c")
            if kind == "Str":
                segments.append(self._record_segment(content, styles, link_target))
            elif kind == "Space":
                segments.append(self._record_segment(" ", styles, link_target))
            elif kind == "SoftBreak" or kind == "LineBreak":
                segments.append(self._record_segment("\n" if kind == "LineBreak" else " ", styles, link_target))
            elif kind == "Emph":
                segments.extend(
                    self._flatten_inlines(content, block_index=block_index, block_type=block_type, styles=styles + ["italic"], link_target=link_target)
                )
            elif kind == "Strong":
                segments.extend(
                    self._flatten_inlines(content, block_index=block_index, block_type=block_type, styles=styles + ["bold"], link_target=link_target)
                )
            elif kind == "Underline":
                segments.extend(
                    self._flatten_inlines(content, block_index=block_index, block_type=block_type, styles=styles + ["underline"], link_target=link_target)
                )
            elif kind == "Code":
                segments.append(self._record_segment(content[1], styles + ["code"], link_target))
            elif kind == "Link":
                attrs, inner, target = content
                url, title = target
                link_styles = styles + ["link"]
                nested_segments = self._flatten_inlines(inner, block_index=block_index, block_type=block_type, styles=link_styles, link_target=url)
                segments.extend(nested_segments)
                self.resources["links"].append(
                    {
                        "text": "".join(seg["text"] for seg in nested_segments).strip(),
                        "target": url,
                        "title": title,
                        "position": {"block_index": block_index},
                    }
                )
            elif kind == "Image":
                attrs, inner, target = content
                url, title = target
                alt_segments = self._flatten_inlines(inner, block_index=block_index, block_type=block_type, styles=styles)
                self.resources["images"].append(
                    {
                        "alt_text": "".join(seg["text"] for seg in alt_segments),
                        "target": url,
                        "title": title,
                        "position": {"block_index": block_index},
                        "attributes": {
                            "identifier": attrs[0],
                            "classes": attrs[1],
                            "kv": dict(attrs[2]),
                        },
                    }
                )
            elif kind == "Span":
                attrs, inner = content
                span_styles = styles + list(attrs[1])
                segments.extend(
                    self._flatten_inlines(inner, block_index=block_index, block_type=block_type, styles=span_styles, link_target=link_target)
                )
            else:
                continue
        return segments

    def _record_segment(self, text: str, styles: List[str], link_target: Optional[str]) -> Dict[str, Any]:
        segment = InlineSegment(text, styles)
        self.inline_segments.append(segment)
        data = segment.to_dict()
        if link_target:
            data["target"] = link_target
        return data

    def _flatten_list_item(self, item: List[Any], block_index: int, position: int, *, ordered: bool) -> Dict[str, Any]:
        walker = BlockWalker()
        nested = walker.walk(item)
        self.inline_segments.extend(walker.inline_segments)
        for key, value in walker.resources.items():
            self.resources[key].extend(value)
        return {
            "position": position,
            "ordered": ordered,
            "blocks": nested,
        }
