"""
JSON Schema definition for standardized document format.
"""

DOCUMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Standardized Document Format",
    "type": "object",
    "required": ["metadata", "content"],
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "created_date": {"type": "string", "format": "date-time"},
                "modified_date": {"type": "string", "format": "date-time"},
                "format": {"type": "string", "enum": ["docx", "doc", "html", "txt"]},
                "language": {"type": "string"},
                "page_count": {"type": "integer"},
                "word_count": {"type": "integer"}
            },
            "required": ["format"]
        },
        "content": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type", "position"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["heading", "paragraph", "list", "table", "image", "link"]
                    },
                    "position": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer"},
                            "page": {"type": "integer"}
                        },
                        "required": ["index"]
                    },
                    "level": {"type": "integer", "minimum": 1, "maximum": 6},
                    "text": {"type": "string"},
                    "style": {
                        "type": "object",
                        "properties": {
                            "bold": {"type": "boolean"},
                            "italic": {"type": "boolean"},
                            "underline": {"type": "boolean"},
                            "color": {"type": "string"},
                            "font_size": {"type": "number"},
                            "font_family": {"type": "string"}
                        }
                    },
                    "items": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "ordered": {"type": "boolean"},
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "headers": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "src": {"type": "string"},
                    "alt": {"type": "string"},
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "href": {"type": "string"},
                    "target": {"type": "string"}
                }
            }
        }
    }
}
