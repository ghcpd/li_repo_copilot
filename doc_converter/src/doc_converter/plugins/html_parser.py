"""HTML parsing plugin shared by several formats."""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Sequence
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

from ..models import (
    DocumentMetadata,
    DocumentModel,
    DocumentPosition,
    HeadingBlock,
    ImageBlock,
    LinkBlock,
    ListBlock,
    ListItem,
    ParagraphBlock,
    TableBlock,
    TableCell,
    TextRun,
)
from ..plugins.base import FormatPlugin


@dataclass(slots=True)
class RunStyle:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    code: bool = False
    color: str | None = None
    background_color: str | None = None
    link_target: str | None = None
    link_title: str | None = None
    link_internal: bool | None = None


class HtmlProcessor:
    """Convert HTML markup into :class:`DocumentModel` entities."""

    def __init__(self, inline_images: bool = False) -> None:
        self.inline_images = inline_images
        self._index = 0
        self._base_path: Optional[Path] = None

    def parse_html(
        self,
        html: str,
        *,
        source_path: str,
        metadata: DocumentMetadata | None = None,
        base_path: Path | None = None,
    ) -> DocumentModel:
        self._index = 0
        self._base_path = base_path.resolve() if base_path else None

        soup = BeautifulSoup(html, "lxml")
        meta = metadata or self._extract_metadata(soup, source_path)
        blocks = []

        body = soup.body or soup
        for node in list(body.children):
            blocks.extend(self._dispatch_node(node))

        self._base_path = None
        return DocumentModel(metadata=meta, content=blocks)

    # ------------------------------------------------------------------
    def _dispatch_node(self, node) -> list:
        if isinstance(node, NavigableString):
            text = node.strip()
            if text:
                return [self._paragraph_from_runs([TextRun(text=text)], style_name=None)]
            return []

        if not isinstance(node, Tag):
            return []

        name = node.name.lower()
        if name in {"script", "style"}:
            return []

        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(name[-1])
            runs = list(self._iter_runs(node))
            text = "".join(run.text for run in runs).strip()
            return [self._heading(text, runs, level, node.get("class"))]

        if name in {"p", "div"}:
            runs = list(self._iter_runs(node))
            if not runs:
                return []
            return [self._paragraph_from_runs(runs, style_name=self._class_name(node))]

        if name in {"ul", "ol"}:
            ordered = name == "ol"
            list_block = self._parse_list(node, ordered)
            return [list_block] if list_block.items else []

        if name == "table":
            table_block = self._parse_table(node)
            return [table_block] if table_block.rows else []

        if name == "img":
            block = self._parse_image(node)
            return [block]

        if name == "a":
            runs = list(self._iter_runs(node, initial_style=self._style_from_tag(node)))
            text = "".join(run.text for run in runs).strip()
            target = node.get("href")
            if not target:
                return []
            is_internal = self._is_internal_link(target)
            position = self._next_position()
            return [
                LinkBlock(
                    text=text or target,
                    target=target,
                    internal=is_internal,
                    spans=runs,
                    position=position,
                )
            ]

        # For container elements, recurse into children to maintain order.
        blocks = []
        for child in node.children:
            blocks.extend(self._dispatch_node(child))
        return blocks

    # ------------------------------------------------------------------
    def _paragraph_from_runs(self, runs: Sequence[TextRun], style_name: str | None) -> ParagraphBlock:
        position = self._next_position()
        return ParagraphBlock(spans=list(runs), style=style_name, position=position)

    def _heading(self, text: str, runs: Sequence[TextRun], level: int, classes: Sequence[str] | None) -> HeadingBlock:
        position = self._next_position()
        style_name = " ".join(classes) if classes else None
        return HeadingBlock(level=level, text=text, spans=list(runs), style=style_name, position=position)

    def _parse_list(self, tag: Tag, ordered: bool) -> ListBlock:
        items = [self._parse_list_item(li) for li in tag.find_all("li", recursive=False)]
        items = [item for item in items if item is not None]
        position = self._next_position()
        return ListBlock(ordered=ordered, items=items, position=position)

    def _parse_list_item(self, item: Tag) -> ListItem | None:
        child_lists: list[tuple[Tag, bool]] = []
        for child in item.find_all(["ul", "ol"], recursive=False):
            ordered = child.name.lower() == "ol"
            child_lists.append((child, ordered))

        for child, _ in child_lists:
            child.extract()

        runs = list(self._iter_runs(item))
        text = "".join(run.text for run in runs).strip()
        if not text and not runs:
            text = item.get_text(strip=True)
            runs = [TextRun(text=text)] if text else []

        children: list[ListItem] = []
        child_order: Optional[bool] = None
        for child, ordered in child_lists:
            sub_list = self._parse_list(child, ordered)
            if child_order is None:
                child_order = sub_list.ordered
            elif child_order != sub_list.ordered:
                child_order = None
            children.extend(sub_list.items)

        if not runs and not children:
            return None

        position = self._next_position()
        return ListItem(
            text=text,
            spans=runs,
            position=position,
            children=children,
            children_ordered=child_order,
        )

    def _parse_table(self, table: Tag) -> TableBlock:
        rows = []
        for r_index, row in enumerate(table.find_all("tr", recursive=False)):
            cells = []
            for c_index, cell in enumerate(row.find_all(["th", "td"], recursive=False)):
                runs = list(self._iter_runs(cell))
                header = cell.name.lower() == "th"
                cells.append(
                    TableCell(
                        row=r_index,
                        column=c_index,
                        spans=runs,
                        header=header,
                    )
                )
            if cells:
                rows.append(cells)
        position = self._next_position()
        return TableBlock(rows=rows, position=position)

    def _parse_image(self, tag: Tag) -> ImageBlock:
        src = tag.get("src")
        alt = tag.get("alt")
        width = self._parse_int(tag.get("width"))
        height = self._parse_int(tag.get("height"))
        mime = None
        data_b64 = None
        resolved_source = self._resolve_source(src)

        if src and src.startswith("data:"):
            mime, data_b64 = self._split_data_uri(src)
        elif self.inline_images and resolved_source and resolved_source.exists():
            data_bytes = resolved_source.read_bytes()
            data_b64 = base64.b64encode(data_bytes).decode("ascii")
            mime = mimetypes.guess_type(str(resolved_source))[0]
            src = str(resolved_source)
        elif resolved_source and resolved_source.exists():
            src = str(resolved_source)

        position = self._next_position()
        return ImageBlock(
            description=alt,
            width_px=width,
            height_px=height,
            content_type=mime,
            data=data_b64,
            source=src,
            position=position,
        )

    # ------------------------------------------------------------------
    def _iter_runs(self, node, initial_style: RunStyle | None = None) -> Iterator[TextRun]:
        style = initial_style or RunStyle()
        for child in getattr(node, "children", []):
            if isinstance(child, NavigableString):
                text = str(child)
                if not text:
                    continue
                yield self._run_from_style(text, style)
                continue

            if not isinstance(child, Tag):
                continue

            name = child.name.lower()
            next_style = self._apply_tag_style(child, style)
            if name == "br":
                yield self._run_from_style("\n", next_style)
                continue

            for run in self._iter_runs(child, next_style):
                yield run

    def _style_from_tag(self, tag: Tag) -> RunStyle:
        return self._apply_tag_style(tag, RunStyle())

    def _run_from_style(self, text: str, style: RunStyle) -> TextRun:
        return TextRun(
            text=text,
            bold=style.bold,
            italic=style.italic,
            underline=style.underline,
            strike=style.strike,
            code=style.code,
            color=style.color,
            background_color=style.background_color,
            link_target=style.link_target,
            link_title=style.link_title,
            link_internal=style.link_internal,
        )

    def _apply_tag_style(self, tag: Tag, base: RunStyle) -> RunStyle:
        name = tag.name.lower()
        style = replace(base)
        if name in {"strong", "b"}:
            style.bold = True
        if name in {"em", "i"}:
            style.italic = True
        if name in {"u", "ins"}:
            style.underline = True
        if name in {"s", "del", "strike"}:
            style.strike = True
        if name == "code" or "code" in tag.get("class", []):
            style.code = True

        # Hyperlinks
        if name == "a":
            href = tag.get("href")
            style.link_target = href
            style.link_title = tag.get("title")
            style.link_internal = self._is_internal_link(href)

        inline_style = tag.get("style")
        if inline_style:
            for fragment in inline_style.split(";"):
                if not fragment.strip():
                    continue
                key, _, value = fragment.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if key == "color":
                    style.color = value
                if key in {"background", "background-color"}:
                    style.background_color = value

        return style

    # ------------------------------------------------------------------
    def _extract_metadata(self, soup: BeautifulSoup, source_path: str) -> DocumentMetadata:
        head = soup.head
        title = head.title.string.strip() if head and head.title and head.title.string else None
        author = None
        created = None
        modified = None
        keywords: list[str] = []
        language = soup.html.get("lang") if soup.html else None

        for meta in soup.find_all("meta"):
            name = (meta.get("name") or meta.get("property") or "").lower()
            content = meta.get("content")
            if not content:
                continue
            if name == "author":
                author = content
            elif name in {"dc.creator", "dc:creator"} and not author:
                author = content
            elif name in {"created", "dc.created", "date"} and not created:
                created = self._parse_datetime(content)
            elif name in {"modified", "dc.modified"} and not modified:
                modified = self._parse_datetime(content)
            elif name in {"keywords", "dc.subject"}:
                keywords.extend([part.strip() for part in content.split(",") if part.strip()])

        return DocumentMetadata(
            title=title,
            author=author,
            created_at=created,
            modified_at=modified,
            keywords=keywords,
            language=language,
            source_path=source_path,
        )

    # ------------------------------------------------------------------
    def _next_position(self) -> DocumentPosition:
        position = DocumentPosition(index=self._index)
        self._index += 1
        return position

    @staticmethod
    def _class_name(tag: Tag) -> str | None:
        classes = tag.get("class")
        if not classes:
            return None
        return " ".join(classes)

    @staticmethod
    def _is_internal_link(href: str | None) -> bool:
        if not href:
            return False
        parsed = urlparse(href)
        if parsed.scheme and parsed.scheme not in {"", "file"}:
            return False
        if parsed.netloc:
            return False
        return True

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        if value is None:
            return None
        value = value.strip().replace("px", "")
        try:
            return int(float(value))
        except ValueError:
            return None

    @staticmethod
    def _split_data_uri(data_uri: str) -> tuple[str | None, str | None]:
        if not data_uri.startswith("data:"):
            return None, None
        header, _, rest = data_uri.partition(",")
        mime_part = header.split(";")[0]
        mime = mime_part[5:] if mime_part.startswith("data:") else None
        return mime, rest or None

    def _resolve_source(self, src: str | None) -> Optional[Path]:
        if not src:
            return None

        parsed = urlparse(src)
        if parsed.scheme and parsed.scheme not in {"file"}:
            return None

        candidate: Optional[Path]
        if parsed.scheme == "file":
            candidate = Path(parsed.path)
        else:
            tentative = Path(src)
            if not tentative.is_absolute() and self._base_path is not None:
                tentative = (self._base_path / tentative).resolve()
            candidate = tentative

        try:
            if candidate and candidate.exists():
                return candidate
        except OSError:
            return None

        return None


class HtmlPlugin(FormatPlugin):
    name = "html"
    extensions = ("html", "htm", "xhtml")
    media_types = ("text/html", "application/xhtml+xml")
    signatures = (
        b"<!DOCTYPE html",
        b"<html",
        b"<HTML",
    )

    def __init__(self, inline_images: bool = False) -> None:
        self.processor = HtmlProcessor(inline_images=inline_images)

    def parse(self, path: Path) -> DocumentModel:
        html = path.read_text(encoding="utf-8", errors="ignore")
        return self.processor.parse_html(html, source_path=str(path), base_path=path.parent)


PLUGINS: list[HtmlPlugin] = [HtmlPlugin()]

