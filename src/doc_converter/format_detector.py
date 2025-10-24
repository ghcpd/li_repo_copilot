"""
Format detection module for identifying document types.
"""

import os
import mimetypes
from typing import Optional


class FormatDetector:
    """Detect document format based on extension and file header."""
    
    # Magic bytes for different file formats
    MAGIC_BYTES = {
        'docx': b'PK\x03\x04',  # ZIP-based format
        'doc': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE2 format
        'html': b'<!DOCTYPE',
        'html_alt': b'<html',
    }
    
    EXTENSION_MAP = {
        '.docx': 'docx',
        '.doc': 'doc',
        '.html': 'html',
        '.htm': 'html',
        '.txt': 'txt',
        '.text': 'txt',
    }
    
    @classmethod
    def detect_format(cls, file_path: str) -> Optional[str]:
        """
        Detect document format from file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Detected format string or None
        """
        # First try extension-based detection
        ext_format = cls._detect_by_extension(file_path)
        
        # Verify with magic bytes if possible
        magic_format = cls._detect_by_magic_bytes(file_path)
        
        # Prefer magic bytes detection, fallback to extension
        return magic_format or ext_format
    
    @classmethod
    def _detect_by_extension(cls, file_path: str) -> Optional[str]:
        """Detect format by file extension."""
        _, ext = os.path.splitext(file_path.lower())
        return cls.EXTENSION_MAP.get(ext)
    
    @classmethod
    def _detect_by_magic_bytes(cls, file_path: str) -> Optional[str]:
        """Detect format by reading file header magic bytes."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)  # Read more bytes for better detection
                
                if header.startswith(cls.MAGIC_BYTES['docx']):
                    return 'docx'
                elif header.startswith(cls.MAGIC_BYTES['doc']):
                    return 'doc'
                
                # Check for HTML more thoroughly
                header_lower = header.lower()
                if (header_lower.startswith(cls.MAGIC_BYTES['html']) or 
                    header_lower.lstrip().startswith(cls.MAGIC_BYTES['html']) or
                    header_lower.startswith(cls.MAGIC_BYTES['html_alt']) or 
                    header_lower.lstrip().startswith(cls.MAGIC_BYTES['html_alt']) or
                    b'<html' in header_lower[:200] or
                    b'<!doctype html' in header_lower[:200]):
                    return 'html'
                    
        except Exception:
            pass
        
        return None
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        Check if file format is supported.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if format is supported, False otherwise
        """
        format_type = cls.detect_format(file_path)
        return format_type in ['docx', 'doc', 'html', 'txt']
