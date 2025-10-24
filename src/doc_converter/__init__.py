"""
Document Converter - A tool for converting multiple document formats to JSON.
"""

from .converter import DocumentConverter
from .schema import DOCUMENT_SCHEMA

__version__ = "1.0.0"
__all__ = ["DocumentConverter", "DOCUMENT_SCHEMA"]
