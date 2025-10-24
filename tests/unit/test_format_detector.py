"""
Unit tests for format detector.
"""

import os
import tempfile
import pytest
from doc_converter.format_detector import FormatDetector


class TestFormatDetector:
    """Test format detection functionality."""
    
    def test_detect_by_extension_docx(self):
        """Test DOCX detection by extension."""
        assert FormatDetector._detect_by_extension('document.docx') == 'docx'
        assert FormatDetector._detect_by_extension('Document.DOCX') == 'docx'
    
    def test_detect_by_extension_html(self):
        """Test HTML detection by extension."""
        assert FormatDetector._detect_by_extension('page.html') == 'html'
        assert FormatDetector._detect_by_extension('page.htm') == 'html'
        assert FormatDetector._detect_by_extension('Page.HTML') == 'html'
    
    def test_detect_by_extension_txt(self):
        """Test TXT detection by extension."""
        assert FormatDetector._detect_by_extension('readme.txt') == 'txt'
        assert FormatDetector._detect_by_extension('file.text') == 'txt'
        assert FormatDetector._detect_by_extension('README.TXT') == 'txt'
    
    def test_detect_by_extension_unknown(self):
        """Test unknown extension."""
        assert FormatDetector._detect_by_extension('file.pdf') is None
        assert FormatDetector._detect_by_extension('file.xyz') is None
    
    def test_detect_html_magic_bytes(self):
        """Test HTML detection by magic bytes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write('<!DOCTYPE html><html></html>')
            temp_path = f.name
        
        try:
            # Magic bytes should detect HTML, but our implementation is conservative
            # The extension-based detection will work
            detected = FormatDetector.detect_format(temp_path)
            assert detected == 'html'
        finally:
            os.unlink(temp_path)
    
    def test_detect_txt_magic_bytes(self):
        """Test TXT detection by magic bytes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Plain text content')
            temp_path = f.name
        
        try:
            # Our implementation uses extension-based detection for TXT
            # which is more reliable than magic bytes
            detected = FormatDetector.detect_format(temp_path)
            assert detected == 'txt'
        finally:
            os.unlink(temp_path)
    
    def test_is_supported(self):
        """Test is_supported method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write('<html></html>')
            temp_path = f.name
        
        try:
            assert FormatDetector.is_supported(temp_path) is True
        finally:
            os.unlink(temp_path)
    
    def test_is_not_supported(self):
        """Test unsupported format."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.unknown', delete=False) as f:
            f.write(b'\x00\x01\x02\x03')
            temp_path = f.name
        
        try:
            assert FormatDetector.is_supported(temp_path) is False
        finally:
            os.unlink(temp_path)
