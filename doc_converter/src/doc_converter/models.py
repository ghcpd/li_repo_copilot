"""Data models for the unified document JSON representation."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, RootModel


class DocumentPosition(BaseModel):
    """Represents the original location of a block within a document."""

    index: int = Field(description="Zero-based index of the block in traversal order.")
    page: Optional[int] = Field(
        default=None,
        description=(
            "One-based page number, when available. Not all parsers can determine this value."
        ),
    )
    offset: Optional[int] = Field(
        default=None,
        description="Character offset inside the page or document section when known.",
    )


class TextRun(BaseModel):
    text: str = Field(description="The textual content of the run.")
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    code: bool = False
    color: Optional[str] = Field(default=None, description="Hex color of the foreground text.")
    background_color: Optional[str] = Field(
        default=None, description="Hex color of the run background if available."
    )
    link_target: Optional[str] = Field(
        default=None, description="When present, denotes the hyperlink target for the run."
    )
    link_title: Optional[str] = Field(
        default=None, description="Optional human readable title of the hyperlink."
    )
    link_internal: Optional[bool] = Field(
        default=None,
        description="Indicates whether the hyperlink points to an internal anchor (True) or external resource (False).",
    )


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    subject: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    language: Optional[str] = None
    source_path: str


class HeadingBlock(BaseModel):
    type: Literal["heading"] = "heading"
    level: int = Field(ge=1, le=6)
    text: str
    spans: list[TextRun] = Field(default_factory=list)
    style: Optional[str] = None
    position: DocumentPosition


class ParagraphBlock(BaseModel):
    type: Literal["paragraph"] = "paragraph"
    spans: list[TextRun]
    style: Optional[str] = None
    position: DocumentPosition


class ListItem(BaseModel):
    text: str
    spans: list[TextRun]
    position: DocumentPosition
    children: list["ListItem"] = Field(default_factory=list, repr=False)
    children_ordered: bool | None = Field(
        default=None,
        description=(
            "Indicates whether child list items originate from an ordered (True), unordered (False), or mixed (None) list."
        ),
    )


class ListBlock(BaseModel):
    type: Literal["list"] = "list"
    ordered: bool
    items: list[ListItem]
    position: DocumentPosition


class TableCell(BaseModel):
    row: int
    column: int
    spans: list[TextRun]
    header: bool = False


class TableBlock(BaseModel):
    type: Literal["table"] = "table"
    rows: list[list[TableCell]]
    position: DocumentPosition


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    description: Optional[str] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    content_type: Optional[str] = None
    data: Optional[str] = Field(
        default=None,
        description=(
            "Base64 encoded representation of the image when inline extraction is enabled."
        ),
    )
    source: Optional[str] = Field(
        default=None,
        description="Path or internal identifier for the image within the document.",
    )
    position: DocumentPosition


class LinkBlock(BaseModel):
    type: Literal["link"] = "link"
    text: str
    target: str
    internal: bool
    spans: list[TextRun] = Field(default_factory=list)
    position: DocumentPosition


class PageBreakBlock(BaseModel):
    type: Literal["page_break"] = "page_break"
    position: DocumentPosition


Block = Annotated[
    HeadingBlock
    | ParagraphBlock
    | ListBlock
    | TableBlock
    | ImageBlock
    | LinkBlock
    | PageBreakBlock,
    Field(discriminator="type"),
]


class DocumentModel(BaseModel):
    metadata: DocumentMetadata
    content: list[Block]

    def as_json_dict(self) -> dict:
        """Return a standard library dict ready for JSON serialisation."""

        return self.model_dump(mode="json")


class DocumentCollection(RootModel[list[DocumentModel]]):
    """Represents the result of a batch conversion."""

    root: list[DocumentModel]


def schema_json(indent: Optional[int] = 2) -> str:
    """Expose the JSON schema for external validation tools."""

    return DocumentCollection.model_json_schema(mode="validation")
