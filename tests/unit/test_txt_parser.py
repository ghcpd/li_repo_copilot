"""
Unit tests for text parser.
"""

import os
import tempfile
import pytest
from doc_converter.parsers.txt_parser import TxtParser


class TestTxtParser:
    """Test plain text parser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TxtParser()
    
    def test_can_parse_txt(self):
        """Test can_parse for TXT files."""
        assert self.parser.can_parse('document.txt') is True
        assert self.parser.can_parse('file.text') is True
        assert self.parser.can_parse('FILE.TXT') is True
    
    def test_cannot_parse_other_formats(self):
        """Test can_parse rejects other formats."""
        assert self.parser.can_parse('document.docx') is False
        assert self.parser.can_parse('page.html') is False
    
    def test_parse_simple_text(self):
        """Test parsing simple text."""
        content = "This is a test document.\n\nThis is a second paragraph."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            assert result['metadata']['format'] == 'txt'
            assert result['metadata']['word_count'] == 10  # "This is a test document. This is a second paragraph."
            assert len(result['content']) == 2
            assert result['content'][0]['type'] == 'paragraph'
            assert 'test document' in result['content'][0]['text']
        finally:
            os.unlink(temp_path)
    
    def test_parse_with_headings(self):
        """Test parsing text with headings."""
        content = "# Main Heading\n\nThis is content.\n\n## Subheading\n\nMore content."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Find headings
            headings = [item for item in result['content'] if item['type'] == 'heading']
            assert len(headings) == 2
            assert headings[0]['level'] == 1
            assert 'Main Heading' in headings[0]['text']
            assert headings[1]['level'] == 2
        finally:
            os.unlink(temp_path)
    
    def test_parse_with_list(self):
        """Test parsing text with lists."""
        content = "* Item 1\n* Item 2\n* Item 3"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Find lists
            lists = [item for item in result['content'] if item['type'] == 'list']
            assert len(lists) == 1
            assert lists[0]['ordered'] is False
            assert len(lists[0]['items']) == 3
        finally:
            os.unlink(temp_path)
    
    def test_parse_with_table(self):
        """Test parsing text with table."""
        content = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Find tables
            tables = [item for item in result['content'] if item['type'] == 'table']
            assert len(tables) == 1
            assert len(tables[0]['headers']) == 2
            assert len(tables[0]['rows']) >= 1
        finally:
            os.unlink(temp_path)
    
    def test_is_heading(self):
        """Test heading detection."""
        assert self.parser._is_heading('# Heading') is True
        assert self.parser._is_heading('## Subheading') is True
        assert self.parser._is_heading('TITLE IN CAPS') is True
        assert self.parser._is_heading('normal text') is False
    
    def test_is_list_item(self):
        """Test list item detection."""
        assert self.parser._is_list_item('* Item') is True
        assert self.parser._is_list_item('- Item') is True
        assert self.parser._is_list_item('+ Item') is True
        assert self.parser._is_list_item('1. Item') is True
        assert self.parser._is_list_item('2) Item') is True
        assert self.parser._is_list_item('normal text') is False
