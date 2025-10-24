from __future__ import annotations

import json
from pathlib import Path

import pytest

from doc_converter.core import DocumentConverter
from .utils import create_sample_docx, libreoffice_conversion


@pytest.fixture()
def sample_paths(tmp_path: Path):
    docx_path = tmp_path / "sample.docx"
    details = create_sample_docx(docx_path)
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("Title\n\nParagraph one.\n\nParagraph two with link http://example.com", encoding="utf-8")
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
        <html>
          <head><title>HTML Sample</title></head>
          <body>
            <h1>HTML Heading</h1>
            <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
            <ul>
              <li>Bullet A</li>
              <li>Bullet B</li>
            </ul>
            <ol>
              <li>Number A</li>
              <li>Number B</li>
            </ol>
            <table>
              <tr><th>H1</th><th>H2</th></tr>
              <tr><td>R1C1</td><td>R1C2</td></tr>
            </table>
            <p><a href="https://example.com">Example</a></p>
            <img src="https://example.com/image.png" alt="Alt" />
          </body>
        </html>
        """,
        encoding="utf-8",
    )
    with libreoffice_conversion(docx_path, ".doc") as converted_doc:
        doc_path = tmp_path / "sample.doc"
        doc_path.write_bytes(converted_doc.read_bytes())
    return {
        "docx": docx_path,
        "doc": doc_path,
        "txt": txt_path,
        "html": html_path,
        "image": details.image_path,
    }


@pytest.mark.parametrize("key", ["docx", "doc", "html", "txt"])
def test_conversion_runs(converter: DocumentConverter, sample_paths, key):
    result = converter.convert_file(sample_paths[key])
    assert "document" in result.output
    assert result.output["document"]["content"], "Content should not be empty"


def test_word_conversion_metadata(converter: DocumentConverter, sample_paths):
    result = converter.convert_file(sample_paths["docx"])
    metadata = result.output["document"]["metadata"]
    assert metadata["title"] == "Sample Document"
    assert "Author A" in metadata["authors"]
    assert result.output["document"]["resources"]["images"], "should capture images"
    assert result.output["document"]["resources"]["links"], "should capture links"


def test_doc_conversion_structure(converter: DocumentConverter, sample_paths):
    result = converter.convert_file(sample_paths["doc"])
    content_types = {entry["type"] for entry in result.output["document"]["content"]}
    assert "heading" in content_types
    assert "paragraph" in content_types
    assert "list" in content_types


def test_html_conversion_lists(converter: DocumentConverter, sample_paths):
    result = converter.convert_file(sample_paths["html"])
    lists = [entry for entry in result.output["document"]["content"] if entry["type"] == "list"]
    assert any(lst.get("ordered") for lst in lists)
    assert any(not lst.get("ordered") for lst in lists)


def test_plain_text_conversion(converter: DocumentConverter, sample_paths):
    result = converter.convert_file(sample_paths["txt"])
    content = result.output["document"]["content"]
    paragraphs = [entry for entry in content if entry["type"] == "paragraph"]
    assert len(paragraphs) >= 2
    assert any("Paragraph one" in segment["text"] for para in paragraphs for segment in para["text_segments"])
