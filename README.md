# Document Converter

A powerful Python tool for converting multiple document formats (DOCX, HTML, TXT) into a standardized JSON format with intelligent structure parsing and an extensible plugin architecture.

## Features

### 🎯 Core Capabilities

- **Multi-Format Support**: Automatically recognize and parse Word (DOCX), HTML, and TXT documents
- **Intelligent Parsing**: Extract document structure including headings, paragraphs, lists, tables, images, and links
- **Standardized Output**: Convert all formats to a unified JSON schema
- **Batch Processing**: Process entire directories of documents at once
- **Extensible Architecture**: Plugin system for adding support for new formats
- **Metadata Extraction**: Capture document title, author, dates, word count, etc.
- **Style Preservation**: Retain important formatting (bold, italic, colors, fonts)

### 📋 Document Structure Recognition

- **Headings**: H1-H6 hierarchy with automatic level detection
- **Paragraphs**: Text content with style preservation
- **Lists**: Ordered and unordered lists with nesting support
- **Tables**: Complete table structure with headers and data
- **Images**: Image metadata including position, size, and alt text
- **Links**: Internal and external link detection with targets

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

### Dependencies

- `python-docx>=0.8.11` - For DOCX parsing
- `beautifulsoup4>=4.12.0` - For HTML parsing
- `lxml>=4.9.0` - XML/HTML processing
- `jsonschema>=4.0.0` - Optional, for validation

## Quick Start

### Command Line Usage

```bash
# Convert a single file
doc-converter input.docx -o output.json

# Convert all files in a directory
doc-converter ./documents/ -b ./output/

# Recursive batch conversion
doc-converter ./documents/ -b ./output/ -r

# List supported formats
doc-converter --list-formats

# With custom plugins
doc-converter input.pdf -o output.json -p ./plugins/

# Verbose mode with validation
doc-converter input.html -o output.json -v --validate
```

### Python API Usage

```python
from doc_converter import DocumentConverter

# Create converter instance
converter = DocumentConverter()

# Convert a single file
result = converter.convert_file('document.docx', 'output.json')

# Batch convert
results = converter.convert_batch(
    input_dir='./documents',
    output_dir='./output',
    recursive=True
)

# Access parsed data
print(f"Title: {result['metadata']['title']}")
print(f"Word count: {result['metadata']['word_count']}")

for item in result['content']:
    if item['type'] == 'heading':
        print(f"H{item['level']}: {item['text']}")
```

## JSON Output Format

The tool produces a standardized JSON structure:

```json
{
  "metadata": {
    "format": "docx",
    "title": "Document Title",
    "author": "Author Name",
    "created_date": "2024-01-01T12:00:00",
    "modified_date": "2024-01-02T14:30:00",
    "word_count": 1500,
    "source_file": "document.docx"
  },
  "content": [
    {
      "type": "heading",
      "position": {"index": 0},
      "level": 1,
      "text": "Main Heading",
      "style": {
        "bold": true,
        "font_size": 24
      }
    },
    {
      "type": "paragraph",
      "position": {"index": 1},
      "text": "Paragraph content here...",
      "style": {
        "italic": false
      }
    },
    {
      "type": "list",
      "position": {"index": 2},
      "ordered": false,
      "items": [
        {"text": "Item 1"},
        {"text": "Item 2"}
      ]
    },
    {
      "type": "table",
      "position": {"index": 3},
      "headers": ["Column 1", "Column 2"],
      "rows": [
        ["Data 1", "Data 2"],
        ["Data 3", "Data 4"]
      ]
    },
    {
      "type": "image",
      "position": {"index": 4},
      "src": "image.png",
      "alt": "Image description",
      "width": 500,
      "height": 300
    },
    {
      "type": "link",
      "position": {"index": 5},
      "text": "Click here",
      "href": "https://example.com",
      "target": "_blank"
    }
  ]
}
```

## Plugin Architecture

Create custom parsers for new formats:

```python
from doc_converter.parsers import BaseParser
from doc_converter import DocumentConverter

class MyCustomParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.supported_formats = ['pdf']
    
    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')
    
    def parse(self, file_path: str):
        result = self._create_base_structure('pdf')
        
        # Your custom parsing logic
        with open(file_path, 'rb') as f:
            # Parse PDF and populate result
            pass
        
        return result

# Register the custom parser
converter = DocumentConverter()
converter.register_parser('pdf', MyCustomParser())

# Now you can convert PDF files
result = converter.convert_file('document.pdf')
```

### Plugin Directory

Place custom parser files in a directory and load them:

```bash
# plugins/markdown_parser.py
doc-converter input.md -o output.json -p ./plugins/
```

## Supported Formats

| Format | Extension | Parser | Features |
|--------|-----------|--------|----------|
| Word | .docx | DocxParser | Full structure, metadata, images |
| HTML | .html, .htm | HtmlParser | Complete DOM parsing, styles |
| Plain Text | .txt | TxtParser | Markdown-style structure detection |

## Advanced Usage

### Validation

```python
converter = DocumentConverter()
result = converter.convert_file('document.docx')

# Validate against schema
is_valid = converter.validate_json(result)
print(f"Valid: {is_valid}")
```

### Custom Plugin Manager

```python
from doc_converter import DocumentConverter
from doc_converter.plugin_manager import PluginManager

# Load plugins from directory
plugin_manager = PluginManager('./plugins')
plugin_manager.load_plugins()

# Create converter with plugins
converter = DocumentConverter()
for format_type in plugin_manager.get_loaded_plugins():
    parser = plugin_manager.create_parser_instance(format_type)
    converter.register_parser(format_type, parser)
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src/doc_converter tests/
```

## Examples

See the `examples/` directory for more usage examples:

- `usage_example.py` - Basic usage patterns
- Plugin examples in `docs/plugin_example.py`

## Architecture

```
src/doc_converter/
├── __init__.py           # Package initialization
├── schema.py             # JSON schema definition
├── converter.py          # Main converter class
├── format_detector.py    # Format detection logic
├── plugin_manager.py     # Plugin system
├── cli.py                # Command-line interface
└── parsers/
    ├── __init__.py
    ├── base_parser.py    # Abstract base class
    ├── docx_parser.py    # Word document parser
    ├── html_parser.py    # HTML parser
    └── txt_parser.py     # Plain text parser
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.