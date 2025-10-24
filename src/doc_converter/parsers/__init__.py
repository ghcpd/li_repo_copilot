"""
Document parsers package.
"""

from .base_parser import BaseParser
from .docx_parser import DocxParser
from .html_parser import HtmlParser
from .txt_parser import TxtParser

__all__ = ['BaseParser', 'DocxParser', 'HtmlParser', 'TxtParser']
